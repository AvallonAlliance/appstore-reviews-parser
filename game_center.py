# -*- encoding: utf-8 -*-
import requests


FIRST_INDEX = 1
LAST_INDEX = 999068
INDEX_STEP = 200


url = 'https://service.gc.apple.com/WebObjects/GKGameStatsService.woa/wa/getLeaderboard'

request_data_template = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>category</key>
	<string>com.gamehivecorp.taptitans.stage</string>
	<key>count</key>
	<integer>%(step)d</integer>
	<key>game</key>
	<dict>
		<key>adam-id</key>
		<integer>940596201</integer>
		<key>bundle-id</key>
		<string>com.gamehivecorp.taptitans</string>
		<key>bundle-version</key>
		<string>1.0.7.1</string>
		<key>external-version</key>
		<integer>811455102</integer>
	</dict>
	<key>player-scope</key>
	<string>all</string>
	<key>starting-rank</key>
	<integer>%(rank)d</integer>
	<key>time-scope</key>
	<string>all-time</string>
</dict>
</plist>
"""

headers = {
    'x-gk-external-version': 811427597,
    'x-gk-device-scale': 2,
    'x-gk-player-id-hash': 1667605,
    'x-gk-adam-id': 940596201,
    'x-gk-push-token': 'B10F2B6CBBA1F6F8A62EFDF7B8E3CBACDCB462076AC0F9501252A169700D0163',
    'x-gk-player-id': 'G:286326677',
    'x-gk-auth-token': '2:28:AQAAAABUsHYpQcRFvmzorL2O8I0MHK5deNsgrt8=:28:AQAAAABUsHYpO7tcCrmzf+MnBVhRB152R6A3oMs=',
    'User-Agent': 'gamed/4.10.17.1.6.13.5.2.1 (iPad3,1; 6.1.3; 10B329; GameKit-781.18)',
    'x-gk-udid': '65c4e39c46beb19d093e7a085a072d4a853a1faa',
    'x-gk-bundle-id': 'com.gamehivecorp.taptitans',
    'x-gk-bundle-version': '1.0.7.1',
    'x-gk-region-format': 'en_US',
}


responses = []

current_index = FIRST_INDEX
i = 0
while current_index <= LAST_INDEX:
    print i
    request_data = request_data_template % {'rank': current_index, 'step': INDEX_STEP}
    response = requests.post('https://service.gc.apple.com/WebObjects/GKGameStatsService.woa/wa/getLeaderboard', data=request_data, headers=headers)
    responses.append(response.text)
    current_index += INDEX_STEP
    i += 1
