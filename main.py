from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
import os
import json

print(f"\n|=RGBSyncWeb - WEB \n|=V-0.9.7\n|=By FireTIA\n")

try:
    with open("Setting.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
except FileNotFoundError:
    print("Файл Setting.json не найден. Используется пароль по умолчанию.")
    settings = {}

password_loging = settings.get("password", "WRGB")
Access_Type = settings.get("Acces_type", "Local")
Manual_IP = settings.get("Manual_IP_setup", "127.0.0.1")
Port_WEB = settings.get("Port_WEB", "5000")

app = Flask(__name__)

app.secret_key = os.urandom(24)

client = OpenRGBClient()
devices = client.devices

device_modes = {device.name: [mode.name for mode in device.modes] for device in devices}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == password_loging: 
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('Error_login.html')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    common_modes = set(device_modes[devices[0].name])
    for device in devices[1:]:
        common_modes &= set(device_modes[device.name])

    return render_template('index.html', devices=[device.name for device in devices], modes=list(common_modes), device_modes=device_modes)

@app.route('/set_color', methods=['POST'])
def set_color():
    data = request.json
    color = RGBColor(data['r'], data['g'], data['b'])
    device_name = data.get('device')
    
    for device in devices:
        if device.name == device_name or device_name == 'All':
            device.set_color(color)
    
    return jsonify({'status': 'success', 'color': data})

@app.route('/turn_off', methods=['POST'])
def turn_off():
    for device in devices:
        device.set_color(RGBColor(0, 0, 0))
    return jsonify({'status': 'success', 'message': 'Lights turned off'})

@app.route('/Open_Documentation', methods=['GET'])
def open_documentation():
    return render_template('doc.html')

@app.route('/set_mode', methods=['POST'])
def set_mode():
    data = request.json
    mode = data.get('mode')
    device_name = data.get('device')

    for device in devices:
        if device.name == device_name or device_name == 'All':
            for m in device.modes:
                if m.name == mode:
                    device.set_mode(m)
                    break

    return jsonify({'status': 'success', 'mode': mode})

@app.route('/set_brightness', methods=['POST'])
def set_brightness():
    data = request.json
    brightness = data.get('brightness')
    device_name = data.get('device')
    
    for device in devices:
        if hasattr(device, 'max_brightness'):
            max_brightness = device.max_brightness
            new_brightness = int((brightness / 100) * max_brightness)
            device.set_brightness(new_brightness)
    
    return jsonify({'status': 'success', 'brightness': brightness})

@app.route('/get_device_info', methods=['GET'])
def get_device_info():
    device_name = request.args.get('device', 'All')
    device_info = []

    for device in devices:
        if device.name == device_name or device_name == 'All':
            active_colors = [color for color in device.colors if color.red or color.green or color.blue]

            if active_colors:
                first_color = active_colors[0]
            else:
                first_color = RGBColor(25, 25, 25)

            device_info.append({
                'name': device.name,
                'color': {'r': first_color.red, 'g': first_color.green, 'b': first_color.blue}
            })

    return jsonify(device_info)

@app.route('/get_device_modes', methods=['GET'])
def get_device_modes():
    device_name = request.args.get('device', 'All')
    available_modes = []

    if device_name == 'All':
        common_modes = set(device_modes[devices[0].name])
        for device in devices[1:]:
            common_modes &= set(device_modes[device.name])
        available_modes = list(common_modes)
    else:
        available_modes = device_modes.get(device_name, [])

    return jsonify(available_modes)

if __name__ == '__main__':
    if Access_Type in ["Global"]:
        print("Вы уверены запустить в широковещание? y/n")
        select = input("> ")
        if select in ["Y", "y", "yes", "Yes", "Да", "да", "Д", "д"]:
            app.run(host='0.0.0.0', port=Port_WEB, debug=True)
        else: 
            print("Вы отказались, изменить настройки можно в 'Setting.json' ")
            exit()
    if Access_Type in ["Local"]:
        app.run(host='127.0.0.1', port=Port_WEB, debug=True)
    if Access_Type in ["Manual_IP"]:
        app.run(host=Manual_IP, port=Port_WEB, debug=True)
    else: 
        print("Похоже возникла ошибка")