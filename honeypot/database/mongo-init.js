// Create honeypot database user if it doesn't exist
print('Creating honeypot database and user...');

db = db.getSiblingDB('admin');

// Create root user if running for the first time
if (!db.getUser(process.env.MONGO_INITDB_ROOT_USERNAME)) {
    db.createUser({
        user: process.env.MONGO_INITDB_ROOT_USERNAME,
        pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
        roles: ["root"]
    });
    print('Root user created');
}

// Create honeypot database and user
db = db.getSiblingDB('honeypot');

db.createUser({
    user: process.env.MONGO_INITDB_ROOT_USERNAME,
    pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
    roles: [
        { role: "readWrite", db: "honeypot" },
        { role: "dbAdmin", db: "honeypot" }
    ]
});

print('Honeypot database user created');

// Initialize required collections
db.createCollection('honeypot_interactions');
db.createCollection('scanAttempts');
db.createCollection('watchList');
db.createCollection('securityBlocklist');
db.createCollection('admin_login_attempts');

print('Initial collections created');

// Create indexes
db.honeypot_interactions.createIndex({ "timestamp": 1 });
db.honeypot_interactions.createIndex({ "ip_address": 1 });
db.honeypot_interactions.createIndex({ "page_type": 1 });
db.honeypot_interactions.createIndex({ "interaction_type": 1 });

db.scanAttempts.createIndex({ "timestamp": 1 });
db.scanAttempts.createIndex({ "clientId": 1 });
db.scanAttempts.createIndex({ "ip": 1 });
db.scanAttempts.createIndex([{ "ip": 1 }, { "timestamp": -1 }]);

db.watchList.createIndex({ "clientId": 1 }, { unique: true });
db.watchList.createIndex({ "ip": 1 });
db.watchList.createIndex({ "severity": 1 });

db.securityBlocklist.createIndex({ "clientId": 1 });
db.securityBlocklist.createIndex({ "ip": 1 });
db.securityBlocklist.createIndex({ "blockUntil": 1 });

db.admin_login_attempts.createIndex({ "ip": 1 });
db.admin_login_attempts.createIndex({ "lastAttempt": 1 });

print('Database initialization completed');
