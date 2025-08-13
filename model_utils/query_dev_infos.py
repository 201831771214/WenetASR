import sounddevice as sd

def get_dev_info():
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f'Device {i}: {device["name"]} ---- {device["max_input_channels"]} ---- {device["max_output_channels"]} ---- {device["default_samplerate"]}')

if __name__ == "__main__":
    get_dev_info()