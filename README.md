# Home Assistant MQTT (with media player)

The default [MQTT](https://www.home-assistant.io/integrations/mqtt/) integration for Home Assistant does not have support for **Media Players**.

This is a fork of the original mqtt component with support for media players.

[![HACS Custom][badge_integration]][link_integration-repo] [![Github stars][badge_integration-stars]][link_integration-repo] [![Github issues][badge_integration-issues]][link_integration-issues]

[![Support me on Github][badge_sponsor]][link_sponsor] [![Follow on Twitter][badge_twitter]][link_twitter]

## Installation

1. Install [HACS (Home Assistant Community Store)](https://hacs.xyz/docs/setup/prerequisites)
2. Add a [custom repository](https://hacs.xyz/docs/faq/custom_repositories) 
3. Look for the mqtt integration and click install

Custom repository details:

- Repository: `svrooij/home-assistant-mqtt-component/`
- Category: `Integration`

## Works with

This modified integration and [Sonos2mqtt](#sonos2mqtt) are both build by [me](https://svrooij.io/) and work perfectly toghether. That does not mean it won't work with another media player that sends out mqtt messages, just send a [PR][link_integration-pr]

### Sonos2mqtt

[![Sonos2mqtt][badge_sonos-mqtt]][link_sonos-mqtt] [![docker pulls][badge_sonos-mqtt-docker]][link_sonos-mqtt-docker] [![sonos2mqtt issues][badge_sonos-mqtt-issues]][link_sonos-mqtt-issues]

The latest beta version of Sonos2mqtt has support for sending mqtt discovery messages. And works perfectly in combination with this MQTT integration with media player support.

Thousands of users are already using this application, according to the amount of Dockerhub pulls.

The most noteworthy feature is support for [notifications](https://svrooij.io/sonos2mqtt/control/notifications.html), which actually restores playback after playing.

## Other media players

By utializing mqtt, and sending the correct messages from the media player you can easily accomplish media player support with local push without the need to touch home assistant. It's just a matter of sending the correct messages.

### Existing Sonos integration

The current [Sonos integration](https://www.home-assistant.io/integrations/sonos/) does not really support **Play this sound and revert back to original**. It only works 25% of the time, messing up the current playlist the rest of the time.

This does not replace the sonos integration (but is can...), you can run both at the same time.

## License

I'm not sure about the license, for now I copied the [License](./License.md) from the the [Home Assistant Repository](https://github.com/home-assistant/core/blob/dev/LICENSE.md). Contact me if this is incorrect.

[badge_integration]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?logo=Home+Assistant+Community+Store&style=for-the-badge
[badge_integration-issues]: https://img.shields.io/github/issues/svrooij/home-assistant-mqtt-component?logo=github&style=for-the-badge
[badge_integration-stars]: https://img.shields.io/github/stars/svrooij/home-assistant-mqtt-component?logo=github&style=for-the-badge

[badge_sonos-mqtt]: https://img.shields.io/badge/sonos-mqtt-blue?style=for-the-badge
[badge_sonos-mqtt-docker]:https://img.shields.io/docker/pulls/svrooij/sonos2mqtt?logo=docker&style=for-the-badge
[badge_sonos-mqtt-issues]: https://img.shields.io/github/issues/svrooij/sonos2mqtt?logo=github&style=for-the-badge
[badge_sonos-mqtt-stars]: https://img.shields.io/github/stars/svrooij/sonos2mqtt?logo=github&style=for-the-badge

[badge_sponsor]: https://img.shields.io/github/sponsors/svrooij?logo=github&style=for-the-badge
[badge_twitter]: https://img.shields.io/twitter/follow/svrooij?logo=twitter&style=for-the-badge

[link_integration-issues]: https://github.com/svrooij/home-assistant-mqtt-component/issues
[link_integration-pr]: https://github.com/svrooij/home-assistant-mqtt-component/pulls
[link_integration-repo]: https://github.com/svrooij/home-assistant-mqtt-component

[link_sonos-mqtt]: https://svrooij.io/sonos2mqtt
[link_sonos-mqtt-docker]: https://hub.docker.com/r/svrooij/sonos2mqtt
[link_sonos-mqtt-issues]: https://github.com/svrooij/sonos2mqtt/issues
[link_sonos-mqtt-repo]: https://github.com/svrooij/sonos2mqtt

[link_sponsor]: https://github.com/sponsors/svrooij
[link_twitter]: https://twitter.com/svrooij
