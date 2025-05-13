# Tinker: Particle Cloud Integration for Home Assistant

This repository provides a Home Assistant add-on that enables seamless integration with the Particle Cloud. With this add-on, you can automatically register webhooks with Particle devices, receive and relay Particle events directly into your Home Assistant instance, and control your Particle devices using automations or scripts.

**Limitations:**
- The add-on currently supports subscribing to a single Particle event at a time (as configured in the options).
- Calling Particle functions (remote procedure calls to devices) is not yet supported, but may be added in a future release.

**Features:**
- **Webhook Management:** The add-on registers and updates webhooks with the Particle Cloud so that your Home Assistant instance can receive events.
- **Event Relay:** Particle device events are forwarded to Home Assistant, which can be used to trigger automations or scripts.
- **Dynamic Configuration:** The add-on uses Home Assistant Supervisor APIs and Bashio to configure itself. The webhook URL is constructed using your Home Assistant's public URL and the add-on's ingress path.
- **Configuration via UI:** Configuration is managed through the Home Assistant UI. The add-on uses tokens for authentication with Home Assistant and the Particle Cloud.


# Options

## PARTICLE_AUTH

To get a particle [user access token](https://docs.particle.io/reference/cloud-apis/access-tokens/), run:

    $ particle token create --never-expires

You will be prompted for your particle.io account credentials, a 2FA code, then be given a user access token:

    ? Using account user@gmail.com
    Please enter your password: [hidden]
    Use your authenticator app on your mobile device to get a login code.
    Lost access to your phone? Visit https://login.particle.io/account-info
    ? Please enter a login code 123456
    New access token never expires
        123456789012345678901234567890

## PARTICLE_EVENT

This is the Particle event to subscribe to. It defaults to `spark/status`.

## HASS_PUBLIC_URL

The public URL of your Home Assistant instance. This is used to construct the webhook URL for the Particle webhook.
