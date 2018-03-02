#!/usr/bin/env python3

import json
import sys

import vk
import tg


def main():
    if len(sys.argv) < 2:
        print('Config filename required')
        return
    with open(sys.argv[1]) as f:
        config = json.load(f)
    t = tg.TelegramPoster(config['telegram']['token'], config['telegram']['channel'])
    v = vk.VkMonitor(config['vk'], t.post)
    v.monitor_forever()


if __name__ == '__main__':
    main()
