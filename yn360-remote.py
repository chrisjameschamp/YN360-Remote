from quart import Quart, request
import asyncio
import subprocess  # For restarting Bluetooth service
from bleak import BleakClient, BleakError, BleakScanner

app = Quart(__name__)

class YN360Controller:
    def __init__(self, address):
        self.address = address
        self.client = BleakClient(address)
        self.sendCharUuid = 'f000aa61-0451-4000-b000-000000000000'
        self.current_color = [255, 255, 255]
        self.powered = False

    async def connect(self):
        while True:
            try:
                self.client = BleakClient(self.address)
                await self.client.connect()
                print("Connected to the device.")
                break  # Exit the loop if connected successfully
            except BleakError as e:
                print(f"Failed to connect: {e}")
                await self.retry_connection()
                await asyncio.sleep(10)  # Wait for 10 seconds before retrying

    async def disconnect(self):
        if self.client is not None:
            await self.client.disconnect()
            print("Disconnected from the device.")
            self.client = None  # Reset client after disconnection

    async def setColor(self, color, color_change=False):
        try:
            if self.client is None or not self.client.is_connected:
                await self.connect()  # Attempt to connect if not already connected
            # Proceed with setting the color if the client is connected
            if self.client is not None and self.client.is_connected:
                await self.client.write_gatt_char(self.sendCharUuid, bytearray([0xae, 0xa1] + color), response=True)
                if color_change:
                    self.current_color = color
            else:
                print("Failed to connect to the device.")
        except BleakError as e:
            print(f"Failed to set color: {e}")
            await self.disconnect()  # Disconnect if error occurs


    async def retry_connection(self):
        # Restart Bluetooth service and retry connection
        try:
            subprocess.run(["sudo", "systemctl", "restart", "bluetooth"], check=True)
        except subprocess.CalledProcessError:
            print("Failed to restart Bluetooth service.")

    async def turnOn(self):
        await self.setColor(self.current_color)
        self.powered = True

    async def turnOff(self):
        await self.setColor([0, 0, 0])
        self.powered = False
    
    async def getColor(self):
        return self.current_color

device_address = "E8:20:6B:56:31:E0"
yn360 = YN360Controller(device_address)

@app.route('/power/on', methods=['GET'])
async def power_on():
    await yn360.turnOn()
    print('Light is turned on')
    return 'Turned On'

@app.route('/power/off', methods=['GET'])
async def power_off():
    await yn360.turnOff()
    print('Light is turned off')
    return 'Turned Off'

@app.route('/power/status', methods=['GET'])
async def power_status():
    # Implement logic to check if the light is on or off and return the appropriate status
    # Example: return 'On' if light is on else 'Off'
    if yn360.powered:
        print('Status: Light is currently on')
        return str(1)
    else:
        print('Status: Light is currently off')
        return str(0)

@app.route('/color/<hex_color>', methods=['GET'])
async def set_color(hex_color):
    # Convert the hexadecimal color to RGB values
    color = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    await yn360.setColor(color, True)
    print(f'Color set to R: {color[0]} G: {color[1]} B: {color[2]}')
    return 'Color set to {}'.format(hex_color)

@app.route('/color/status', methods=['GET'])
async def color_status():
    # Get the current color
    current_color = await yn360.getColor()
    print(f'Status: Light color is currently R: {current_color[0]} G: {current_color[1]} B: {current_color[2]}')

    # Convert the current color to a hexadecimal string
    hex_color = ''.join(format(c, '02x') for c in current_color)
    return hex_color

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
