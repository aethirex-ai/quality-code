import json
from pathlib import Path
import tempfile
import unittest
from broker import validate_request

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'single'
        self.root.mkdir()
        (self.root/'index.html').write_text('<h1>single</h1>')
        self.other = self.base/'worker'
        self.other.mkdir()
        (self.other/'secret.html').write_text('other condition')
        (self.root/'leak.html').symlink_to(self.other/'secret.html')

    def render(self, **extra):
        return validate_request(dict(op='render',page='index.html',viewport=375,**extra),self.root)

    def test_valid_local_page(self):
        for width in (375,1440):
            self.assertEqual(validate_request({'op':'render','page':'index.html','viewport':width}, self.root),('index.html',width))

    def test_traversal_urls_and_cross_condition_refused(self):
        for page in ('../worker/secret.html','%2e%2e/worker/secret.html','leak.html',
                     '/index.html','https://example.com/index.html','file:///tmp/index.html',
                     '//example.com/index.html','index.html?q=x','index.html#x',
                     'x\\index.html','%252e%252e/secret.html','.env.html'):
            with self.subTest(page=page), self.assertRaises(ValueError):
                validate_request({'op':'render','page':page,'viewport':375}, self.root)

    def test_viewport_and_fields_refused(self):
        for width in (0,374,376,1920,'375',True):
            with self.subTest(width=width), self.assertRaises(ValueError):
                validate_request({'op':'render','page':'index.html','viewport':width},self.root)
        for field in ('root','condition','script','url','output','oracle','grade'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_request({'op':'render','page':'index.html','viewport':375,field:'x'},self.root)

    def test_invalid_actions_and_sizes_refused(self):
        bad_actions = ([{"op":"evaluate","selector":"body"}],
            [{"op":"press","selector":"body","value":"Meta+A"}],
            [{"op":"fill","selector":"x"*201,"value":"a"}],
            [{"op":"fill","selector":"input","value":"a"*301}],
            [{"op":"click","selector":"button","script":"x"}],
            [{"op":"click","selector":"button"}]*13)
        for actions in bad_actions:
            with self.subTest(actions=actions),self.assertRaises(ValueError):
                validate_request({'op':'render','page':'index.html','viewport':375,'actions':actions},self.root)
        validate_request({'op':'render','page':'index.html','viewport':375,'actions':[{'op':'fill','selector':'input','value':'hello'},{'op':'press','selector':'input','value':'Tab'},{'op':'scroll','selector':'footer'}]},self.root)

    def test_history_bounded_relative_and_no_symlink(self):
        import os
        from types import SimpleNamespace
        from broker import record_preview
        fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        self.addCleanup(os.close,fd)
        server=SimpleNamespace(root=self.root,root_fd=fd)
        record_preview(server,{'op':'render','page':'index.html','viewport':375,'actions':[{'op':'scroll','selector':'footer'}]},
            {'ok':True,'screenshot':str(self.root/'.preview-output/a.png'),'errors':[],'horizontalOverflow':False})
        event=json.loads((self.root/'.preview-events.jsonl').read_text())
        self.assertEqual(event['result']['screenshot'],'.preview-output/a.png')
        record_preview(server,{'op':'render','page':'x'*20000},{'ok':False,'error':'x'*20000})
        self.assertTrue(all(len(x.encode())<=16384 for x in (self.root/'.preview-events.jsonl').read_text().splitlines()))
        (self.root/'.preview-events.jsonl').unlink()
        (self.root/'.preview-events.jsonl').symlink_to(self.other/'secret.html')
        with self.assertRaises(OSError): record_preview(server,{'op':'render'},{'ok':False})

    def test_unicode_response_is_bounded(self):
        from broker import encode_response
        self.assertLessEqual(len(encode_response({'text':'🌟'*20000})),16384)
        self.assertFalse(json.loads(encode_response({'text':'🌟'*20000}))['ok'])

    def test_ready_contract(self):
        self.assertIsNone(validate_request({'op':'ready'},self.root))
        with self.assertRaises(ValueError):
            validate_request({'op':'ready','page':'index.html'},self.root)


class SnapshotTests(unittest.TestCase):
    def test_four_original_photos_fit_and_oversize_file_refused(self):
        import os
        from types import SimpleNamespace
        from unittest.mock import patch
        from broker import Broker
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            root=Path(temp)
            (root/'index.html').write_text('<h1>photos</h1>')
            for i in range(4):
                with (root/f'photo-{i}.jpg').open('wb') as image: image.truncate(6*1024*1024)
            fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            self.addCleanup(os.close,fd)
            server=SimpleNamespace(root_fd=fd,node='node',module='playwright',renderer=Path('render.mjs'))
            def fake_run(args,**kwargs):
                payload=json.loads(kwargs['input'])
                self.assertEqual(len(payload['assets']),5)
                self.assertEqual(len(payload['assets']['photo-0.jpg']),8*1024*1024)
                return SimpleNamespace(returncode=0,stdout='{}',stderr='')
            with patch('broker.subprocess.run',side_effect=fake_run):
                Broker.call_renderer(server,{'op':'render','page':'index.html','viewport':375})
            with (root/'too-large.jpg').open('wb') as image: image.truncate(12*1024*1024+1)
            with self.assertRaises(ValueError):
                Broker.call_renderer(server,{'op':'render','page':'index.html','viewport':375})

    def test_descriptor_snapshot_refuses_symlinks_and_stays_at_fixed_root(self):
        import os
        from types import SimpleNamespace
        from unittest.mock import patch
        from broker import Broker
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            base = Path(temp)
            root = base/'single'
            root.mkdir()
            (root/'index.html').write_text('<h1>single</h1>')
            other = base/'worker'
            other.mkdir()
            (other/'secret.html').write_text('worker private page')
            (root/'leak.html').symlink_to(other/'secret.html')
            (root/'linked').symlink_to(other, target_is_directory=True)
            rootfd = os.open(root, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            self.addCleanup(os.close, rootfd)
            broker = SimpleNamespace(root_fd=rootfd,node='node',module='playwright',renderer=Path('render.mjs'))
            def fake_run(args, **kwargs):
                payload = json.loads(kwargs['input'])
                self.assertEqual(set(payload['assets']), {'index.html'})
                self.assertNotIn('root', payload)
                return SimpleNamespace(returncode=0,stdout='{"ready":true}',stderr='')
            with patch('broker.subprocess.run', side_effect=fake_run):
                Broker.call_renderer(broker, {'op':'render','page':'index.html','viewport':375,'screenshot':'staged.png'})

class MailboxTests(unittest.TestCase):
    def test_atomic_roundtrip_refusals_and_cleanup(self):
        import os
        import threading
        import time
        from types import SimpleNamespace
        from broker import serve_mailbox
        from client import mailbox_request
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            root=Path(temp)
            rootfd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            server=SimpleNamespace(root_fd=rootfd,root=root,ready=True)
            stop=threading.Event()
            thread=threading.Thread(target=serve_mailbox,args=(server,stop),daemon=True)
            thread.start()
            try:
                for _ in range(100):
                    if (root/'.preview-mailbox').exists(): break
                    time.sleep(.01)
                self.assertEqual(mailbox_request(root,{'op':'ready'}),{'ok':True,'ready':True,'viewports':[375,1440]})
                with self.assertRaises(RuntimeError): mailbox_request(root,{'op':'ready','value':'x'*5000})
                rejected=mailbox_request(root,{'op':'render','condition':'worker','viewport':375})
                self.assertFalse(rejected['ok'])
                self.assertEqual(list((root/'.preview-mailbox').iterdir()),[])
                event=json.loads((root/'.preview-events.jsonl').read_text())
                self.assertFalse(event['result']['ok'])
                self.assertEqual(set(event),{'timestamp','request','result'})
                # A symlink cannot redirect the protocol namespace.
                (root/'.preview-mailbox').rmdir()
                other=root/'other'
                other.mkdir()
                (root/'.preview-mailbox').symlink_to(other,target_is_directory=True)
                with self.assertRaises(OSError): mailbox_request(root,{'op':'ready'})
            finally:
                stop.set()
                thread.join(2)
                os.close(rootfd)

if __name__=='__main__': unittest.main()
