import serial
import paho.mqtt.client as mqtt

# =========== НАСТРОЙКИ (Поменяйте порт USB, если нужно) ===========
SERIAL_PORT = '/dev/cu.usbserial-10'  # На Windows: 'COM3' или 'COM4'
BAUD_RATE = 115200

# Настройки облака (Должны совпадать с сервером Railway)
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "openmower/cloud_hils_mk/command"
# =================================================================

# 1. Открываем физический USB порт к Ардуино
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    print(f"✅ Успешно подключено к Ардуино на {SERIAL_PORT}")
except Exception as e:
    print(f"❌ Ошибка подключения USB: {e}")
    print("Проверьте кабель или измените SERIAL_PORT в файле!")
    arduino = None

# 2. Функция, которая срабатывает, когда прилетает команда из Облака
def on_message(client, userdata, message):
    cmd_str = message.payload.decode('utf-8')
    print(f"☁️ Получено из Облака:\n{cmd_str.strip()}")
    
    # 3. Мгновенно передаем текст по кабелю в моторы
    if arduino and arduino.is_open:
        arduino.write(cmd_str.encode('utf-8'))

# Подключаемся к интернет-радиостанции
client = mqtt.Client()
client.on_message = on_message

print(f"🌐 Подключение к облаку {BROKER}...")
client.connect(BROKER, PORT, 60)
client.subscribe(TOPIC)

print("🚀 Скрипт-мост запущен! Жду команды с Railway (Foxglove).")
print("Для выхода нажмите Ctrl+C")

# Крутим бесконечный цикл слушания интернета
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\nОтключение...")
    if arduino:
        arduino.close()
