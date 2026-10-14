CREATE TABLE catalogue_activity (id TEXT PRIMARY KEY, serviceId TEXT NOT NULL, serviceName TEXT NOT NULL, actorId TEXT NOT NULL REFERENCES user(id), actorName TEXT NOT NULL, action TEXT NOT NULL, createdAt TEXT NOT NULL);
CREATE INDEX catalogue_activity_service ON catalogue_activity(serviceId,createdAt);
