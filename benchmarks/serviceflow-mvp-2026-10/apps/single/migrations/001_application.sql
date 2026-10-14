CREATE TABLE user_roles (
 userId TEXT PRIMARY KEY REFERENCES user(id) ON DELETE CASCADE,
 role TEXT NOT NULL CHECK(role IN ('customer','provider','admin'))
);
CREATE TABLE services (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL, price TEXT NOT NULL,
 category TEXT NOT NULL CHECK(category IN ('repair','garden','painting','cleaning')),
 active INTEGER NOT NULL CHECK(active IN (0,1)), version INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE requests (
 id TEXT PRIMARY KEY, customerId TEXT NOT NULL REFERENCES user(id), serviceId TEXT NOT NULL REFERENCES services(id) ON DELETE RESTRICT,
 serviceName TEXT NOT NULL, serviceDescription TEXT NOT NULL, servicePrice TEXT NOT NULL,
 description TEXT NOT NULL, location TEXT NOT NULL, preferredFrom TEXT NOT NULL, preferredTo TEXT NOT NULL DEFAULT '',
 contactName TEXT NOT NULL, contactEmail TEXT NOT NULL, contactPhone TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('New','Reviewing','Quoted','Booked','Completed','Declined')),
 version INTEGER NOT NULL DEFAULT 0, createdAt TEXT NOT NULL, updatedAt TEXT NOT NULL
);
CREATE INDEX requests_owner ON requests(customerId, createdAt);
CREATE INDEX requests_status ON requests(status, createdAt);
CREATE TABLE activity (
 id INTEGER PRIMARY KEY AUTOINCREMENT, requestId TEXT REFERENCES requests(id),
 serviceId TEXT REFERENCES services(id) ON DELETE SET NULL,
 actorId TEXT NOT NULL REFERENCES user(id), actorName TEXT NOT NULL, action TEXT NOT NULL, createdAt TEXT NOT NULL
);
CREATE INDEX activity_request ON activity(requestId, id);
CREATE TABLE mutation_receipts (
 actorId TEXT NOT NULL REFERENCES user(id), key TEXT NOT NULL, fingerprint TEXT NOT NULL, result TEXT NOT NULL,
 createdAt TEXT NOT NULL, PRIMARY KEY(actorId,key)
);
