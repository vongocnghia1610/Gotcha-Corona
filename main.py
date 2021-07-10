import asyncio

import cv2
import numpy as np
import websockets
import base64
import json
import os
# CORONA_TEMPLATE_PATH = os.path.dirname(os.path.abspath(__file__)) + '/characters/character-1.png'

CORONA_TEMPLATE_PATH = os.path.dirname(os.path.abspath(__file__)) + '/characters/character-1.png'

CORONA_SCALE_RATIO = 0.5

corona_template_image = cv2.imread(CORONA_TEMPLATE_PATH, 0)

corona_template_image = cv2.resize(corona_template_image, None, fx=CORONA_SCALE_RATIO, fy=CORONA_SCALE_RATIO)
hinhbs = []
hinhbs.append(cv2.imread(r'D:/CodePython/gotcha-corona-player/characters/character-6.png'))
hinhbs.append(cv2.imread(r'D:/CodePython/gotcha-corona-player/characters/character-5.png'))
hinh = []

hinh.append(cv2.imread(r'D:/CodePython/gotcha-corona-player/characters/character-4.png'))
hinh.append(cv2.imread(r'D:/CodePython/gotcha-corona-player/characters/character-3.png'))
hinh.append(cv2.imread(r'D:/CodePython/gotcha-corona-player/characters/character-2.png'))
hinh.append(cv2.imread(r'D:/CodePython/gotcha-corona-player/characters/character-1.png'))

def catch_doctor(wave_image, threshold=0.6):
    wave_image_gray = cv2.cvtColor(wave_image, cv2.COLOR_BGRA2GRAY)
    width, height = corona_template_image.shape[::-1]
    doctors = []

    # template_gray = cv2.cvtColor(hinh, cv2.COLOR_BGRA2GRAY)
    # cv2.imwrite(os.path.join(f'waves/test/', 'nghia1.jpg'), template_gray)
    for hinhmau in hinhbs:
        hinhmau = cv2.resize(hinhmau, None, fx=CORONA_SCALE_RATIO, fy=CORONA_SCALE_RATIO)
        template_gray = cv2.cvtColor(hinhmau, cv2.COLOR_BGRA2GRAY)

        res = cv2.matchTemplate(wave_image_gray, template_gray, cv2.TM_CCOEFF_NORMED)

        # min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        # if max_val > threshold:
        #     return []

        # top_left = max_loc
        # bottom_right = (top_left[0] + width, top_left[1] + height)
        loc = np.where( res >= threshold)
        for pt in zip(*loc[::-1]):
            doctors.append([pt,(pt[0] + width, pt[1] + height)])

    # return [[top_left, bottom_right]]
    return doctors

def catch_corona(wave_image, threshold=0.75):
    wave_image_gray = cv2.cvtColor(wave_image, cv2.COLOR_BGRA2GRAY)
    width, height = corona_template_image.shape[::-1]
    coronas = []

    # template_gray = cv2.cvtColor(hinh, cv2.COLOR_BGRA2GRAY)
    # cv2.imwrite(os.path.join(f'waves/test/', 'nghia1.jpg'), template_gray)
    for hinhmau in hinh:
        hinhmau = cv2.resize(hinhmau, None, fx=CORONA_SCALE_RATIO, fy=CORONA_SCALE_RATIO)
        template_gray = cv2.cvtColor(hinhmau, cv2.COLOR_BGRA2GRAY)

        res = cv2.matchTemplate(wave_image_gray, template_gray, cv2.TM_CCOEFF_NORMED)

        # min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        # if max_val > threshold:
        #     return []

        # top_left = max_loc
        # bottom_right = (top_left[0] + width, top_left[1] + height)
        loc = np.where( res >= threshold)
        for pt in zip(*loc[::-1]):
            coronas.append([pt,(pt[0] + width, pt[1] + height)])

    # return [[top_left, bottom_right]]
    return coronas

def base64_to_image(base64_data):
    encoded_data = base64_data.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

    return img

async def play_game(websocket, path):
    print('Corona Killer is ready to play!')
    catchings = []
    last_round_id = ''
    wave_count = 0
    
    while True:

        ### receive a socket message (wave)
        try:
            data = await websocket.recv()
        except Exception as e:
            print('Error: ' + e)
            break

        json_data = json.loads(data)

        ### check if starting a new round
        if json_data["roundId"] != last_round_id:
            print(f'> Catching corona for round {json_data["roundId"]}...')
            last_round_id = json_data["roundId"]

        ### catch corona in a wave image
        wave_image = base64_to_image(json_data['base64Image'])
        doctors = catch_doctor(wave_image)

        results = catch_corona(wave_image)

        ### save result image file for debugging purpose
        for result in results:
            cv2.rectangle(wave_image, result[0], result[1], (0, 0, 255), 2)
        
        # waves_dir = f'waves/{last_round_id}/'
        # if not os.path.exists(waves_dir):
        #     os.makedirs(waves_dir)
        # waves_dir = f'waves/Tu/'
        # if not os.path.exists(waves_dir):
        #     os.makedirs(waves_dir)    
        # cv2.imwrite(os.path.join(waves_dir, f'{json_data["waveId"]}.jpg'), wave_image)

        print(f'>>> Wave #{wave_count:03d}: {json_data["waveId"]}')
        wave_count = wave_count + 1
        ketqua=[]
        for result in results:
            i=0

            for doctor in doctors:
                if(((result[0][0] + result[1][0]) / 2 > doctor[0][0] and (result[0][0] + result[1][0]) / 2 < doctor[0][0])
                or ((result[0][1] + result[1][1]) / 2 > doctor[0][1] and (result[0][1] + result[1][1]) / 2 < doctor[1][1])):
                    break
                else :
                    i=i+1
            if(len(doctors)==i):
                ketqua.append(result)
                   

        ### store catching positions in the list
        catchings.append({
            "positions": [
                
                {"x": (kq[0][0] + kq[1][0]) / 2, "y": (kq[0][1] + kq[1][1]) / 2} for kq in ketqua
            ],
            "waveId": json_data["waveId"]
        })

        ### send result to websocket if it is the last wave
        if json_data["isLastWave"]:
            round_id = json_data["roundId"]
            print(f'> Submitting result for round {round_id}...')

            json_result = {
                "roundId": round_id,
                "catchings": catchings,
            }

            await websocket.send(json.dumps(json_result))
            print('> Submitted.')

            catchings = []
            wave_count = 0


start_server = websockets.serve(play_game, "localhost", 8765, max_size=100000000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()