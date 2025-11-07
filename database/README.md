# Database Directory

This folder contains all SQL schema, seed data, and migration files
for the Virtual Truck Loader project.

## Initialize
```bash
python database/scripts/init_db.py
```

## Reset
```bash
python database/scripts/reset_db.py
```

## Migrations
- Each file in `/migrations` is applied in order.
- Use semantic versioning for schema updates

## Runtime
The Unity application will copy this `warehouse.db` to its persistent data path on first launch.