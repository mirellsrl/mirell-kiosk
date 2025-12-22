# Events Configuration Guide

## Overview

The Mirell Kiosk now supports multiple event configurations through a JSON-based configuration system. Instead of using a single environment variable for authentication, you can now define multiple events with their own:

- **Password**: Device authentication key
- **Tag Prefix**: Custom tag prefix for contacts created at this event
- **Welcome Message**: Personalized greeting message displayed on the kiosk
- **Custom Prizes**: Optional event-specific prize configuration

## Configuration File Structure

The configuration is stored in `events_config.json` in the root directory:

```json
{
  "events": {
    "event-key-1": {
      "password": "device-password",
      "tag_prefix": "event-tag-prefix",
      "welcome_message": "Welcome message displayed on kiosk",
      "prizes": [
        {
          "name": "Prize Name",
          "description": "Prize Description",
          "probability": 25,
          "tag": "prize-tag"
        }
      ]
    }
  }
}
```

## Configuration Parameters

### Event Key
- **Type**: String
- **Description**: Unique identifier for the event (used internally)
- **Example**: `"fiera-2025"`, `"fiera-mamma"`

### Password
- **Type**: String
- **Description**: The device authentication code entered at the kiosk to unlock it for a specific event
- **Example**: `"fiera2025"`

### Tag Prefix
- **Type**: String
- **Description**: Prefix automatically added to all tags created for contacts at this event
- **Example**: `"fiera-2025"`, `"fiera-mamma"`
- **Note**: Client type tags will use this prefix (e.g., `fiera-2025-sposa`, `fiera-mamma-mamma-sposa`)

### Welcome Message
- **Type**: String
- **Description**: Custom welcome message displayed on the kiosk screen
- **Example**: `"Benvenuto alla Fiera 2025!"`, `"Benvenuta mamma! Gioca e vinci bellissimi premi!"`

### Prizes (Optional)
- **Type**: Array of objects
- **Description**: Custom prize configuration for the event (if not specified, defaults to `fiera_prizes.json`)
- **Prize Properties**:
  - `name` (String): Display name of the prize
  - `description` (String): Description shown when user wins
  - `probability` (Number): Weight for random selection (relative probability)
  - `tag` (String): Tag added to contact when this prize is won

## Example Configuration

```json
{
  "events": {
    "fiera-2025": {
      "password": "fiera2025",
      "tag_prefix": "fiera-2025",
      "welcome_message": "Benvenuto alla Fiera 2025!",
      "prizes": [
        {
          "name": "Tote Bag",
          "description": "Hai vinto una elegante Tote Bag Mirell",
          "probability": 85,
          "tag": "tote-bag"
        },
        {
          "name": "Penna",
          "description": "Hai vinto una penna personalizzata Mirell",
          "probability": 10,
          "tag": "penna"
        },
        {
          "name": "Riparazione Gratuita",
          "description": "Ripara gratuitamente il tuo abito",
          "probability": 5,
          "tag": "fiera-riparazione-gratuita"
        }
      ]
    },
    "fiera-mamma": {
      "password": "mamma2025",
      "tag_prefix": "fiera-mamma",
      "welcome_message": "Benvenuta mamma! Gioca e vinci bellissimi premi!",
      "prizes": [
        {
          "name": "Tote Bag Premium",
          "description": "Hai vinto una esclusiva Tote Bag Premium Mirell",
          "probability": 70,
          "tag": "tote-bag-premium"
        },
        {
          "name": "Sciarpa Mirell",
          "description": "Hai vinto una bellissima sciarpa esclusiva Mirell",
          "probability": 20,
          "tag": "sciarpa"
        },
        {
          "name": "Voucher Sconto",
          "description": "Hai vinto un voucher sconto del 20% sul prossimo acquisto",
          "probability": 10,
          "tag": "voucher-20"
        }
      ]
    }
  }
}
```

## How It Works

1. **Device Authentication**: When a device accesses `/fiera/auth`, it enters a password
2. **Event Lookup**: The system searches `events_config.json` to find the matching password
3. **Event Selection**: Once matched, the device is authorized for that specific event
4. **Custom Configuration**: All subsequent requests use that event's configuration:
   - Welcome message displayed on the form
   - Tag prefix applied to all created contacts
   - Custom prizes (if defined) for the game

## Migration from Environment Variables

### Old Method (DEPRECATED)
```bash
FIERA_DEVICE_KEY=secret-key
```

### New Method
Add to `events_config.json`:
```json
{
  "events": {
    "my-event": {
      "password": "secret-key",
      "tag_prefix": "my-event",
      "welcome_message": "Welcome!"
    }
  }
}
```

## Adding New Events

To add a new event:

1. Open `events_config.json`
2. Add a new event object under the `events` key:
```json
{
  "events": {
    "existing-event": { ... },
    "new-event": {
      "password": "new-password",
      "tag_prefix": "new-event-tag",
      "welcome_message": "Custom welcome message"
    }
  }
}
```
3. Save the file
4. The kiosk will automatically pick up the new configuration (no restart needed)

## Default Prizes

If an event doesn't specify custom prizes, the system falls back to `fiera_prizes.json`. This allows you to:
- Define global default prizes once
- Override them per-event when needed

## Tags and Data Organization

All contacts created at an event are tagged with:
1. The event's tag prefix (e.g., `fiera-2025`)
2. A client-type tag (e.g., `fiera-2025-sposa`)
3. Additional tags based on game outcome (e.g., `partita-effettuata`, `tote-bag`)

This allows you to:
- Filter contacts by event in SquaddCRM
- Track which prizes were won
- Measure event engagement

## Troubleshooting

### Configuration File Not Found
**Error**: "events_config.json not found. Please create the configuration file."
**Solution**: Create `events_config.json` in the root directory with at least one event

### Invalid JSON
**Error**: "Invalid JSON in events_config.json"
**Solution**: Validate your JSON syntax using a JSON validator

### Password Not Matching
**Error**: "Codice dispositivo non valido."
**Solution**: 
- Verify the password in `events_config.json`
- Check that the password entered on the device exactly matches

### Configuration Not Updating
**Solution**: The configuration is loaded fresh on each authentication, so changes take effect immediately after saving `events_config.json`
