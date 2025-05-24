from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time
import os

input_button_pins = [28, 27, 26, 22, 20, 23, 21, 2]
input_buttons = [Pin(pin, Pin.IN, Pin.PULL_UP) for pin in input_button_pins]

i2c = I2C(0, scl=Pin(1), sda=Pin(0))
oled = SSD1306_I2C(128, 32, i2c)

sec = False
door = False
prev_state = None
display_mode = 0
mode_timer = time.ticks_ms()

def load_state():
    global coin_inserted, coin_dispensed, button3_count, button4_count, button5_count, now_game_count
    try:
        with open("state.txt", "r") as f:
            data = f.read().split(',')
            coin_inserted = int(data[0])
            coin_dispensed = int(data[1])
            button3_count = int(data[2])
            button4_count = int(data[3])
            button5_count = int(data[4])
            now_game_count = int(data[5])
    except:
        reset_state()

def reset_state():
    global coin_inserted, coin_dispensed, button3_count, button4_count, button5_count, now_game_count, last_saved_values
    coin_inserted = 0
    coin_dispensed = 0
    button3_count = 0
    button4_count = 0
    button5_count = 0
    now_game_count = 0
    last_saved_values = (coin_inserted, coin_dispensed, button3_count, button4_count, button5_count, now_game_count)
    save_state()
    update_oled()

def save_state():
    global last_saved_values
    current_state = (coin_inserted, coin_dispensed, button3_count, button4_count, button5_count, now_game_count)
    if current_state != last_saved_values:
        with open("state.txt", "w") as f:
            f.write(f"{coin_inserted},{coin_dispensed},{button3_count},{button4_count},{button5_count},{now_game_count}")
        last_saved_values = current_state

def update_oled():
    global oled, i2c
    try:
        oled.fill(0)
        percentage = int((coin_dispensed / coin_inserted) * 100) if coin_inserted > 0 else 0

        if display_mode == 0:
            oled.text(f"G/ALL: {coin_inserted // 3} G", 0, 0)
            oled.text(f"Diff: {coin_dispensed - coin_inserted}", 0, 10)
            oled.text(f"   {percentage}%", 0, 20)
        elif display_mode == 1:
            oled.hline(14, 16, 100, 1)
            bar_width = min(50, abs(percentage) * 50 // 500)
            oled.text(f"{percentage}%", 54, 20)
            if percentage > 0:
                oled.fill_rect(64, 10, bar_width, 8, 1)
            elif percentage < 0:
                oled.fill_rect(64 - bar_width, 10, bar_width, 8, 1)
        elif display_mode == 2:
            oled.text(f"BONUS: {button4_count}", 0, 0)
            oled.text(f"AT: {button5_count}", 0, 10)
            oled.text(f"GAME: {now_game_count} G", 0, 20)

        oled.show()
        
    except OSError as e:
        print("OLED Connection error:", e)
        print("Try reconnect...")
        try:
            time.sleep(0.5)
            i2c = I2C(0, scl=Pin(1), sda=Pin(0))
            devices = i2c.scan()
            if not devices:
                raise Exception("OLED device not found")
            addr = devices[0]
            print(f"Reinitialize device on {hex(addr)} ")
            oled = SSD1306_I2C(128, 32, i2c, addr=addr)
            oled.fill(0)
            oled.text("Reinitialize Success", 0, 0)
            oled.show()
        except Exception as e2:
            print("Reconnect failed:", e2)
            save_state()
            
def print_and_update_state():
    global prev_state
    current_state = (coin_inserted, coin_dispensed, button3_count, button4_count, button5_count, now_game_count, sec, door)
    if current_state != prev_state:
        print(f"{','.join(map(str, current_state))}")
        update_oled()
        prev_state = current_state

def handle_interrupt(pin):
    global coin_inserted, coin_dispensed, button3_count, button4_count, button5_count, now_game_count, sec, door
    time.sleep_ms(50) 
    pin_index = input_buttons.index(pin)

    if not pin.value():
        if pin_index == 6:
            coin_inserted += 1
            if coin_inserted % 3 == 0:
                now_game_count += 1
        elif pin_index == 5:
            coin_dispensed += 1
        elif pin_index == 4:
            button3_count += 1
            now_game_count = 0
        elif pin_index == 3:
            button4_count += 1
            now_game_count = 0
        elif pin_index == 2:
            button5_count += 1
        elif pin_index == 7:
            reset_state()
        elif pin_index == 1:
            sec = True
        elif pin_index == 0:
            door = True
    else:
        if pin_index in [4, 3, 2]:
            now_game_count = 0
        elif pin_index == 1:
            sec = False
        elif pin_index == 0:
            door = False

    print_and_update_state()

load_state()
last_saved_values = (coin_inserted, coin_dispensed, button3_count, button4_count, button5_count, now_game_count)
print_and_update_state()

for button in input_buttons:
    button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=handle_interrupt)

last_save_time = time.ticks_ms()

while True:
    time.sleep(0.3)
    if time.ticks_diff(time.ticks_ms(), last_save_time) > 30000:
        save_state()
        last_save_time = time.ticks_ms()

    if time.ticks_diff(time.ticks_ms(), mode_timer) > 3000:
        display_mode = (display_mode + 1) % 3
        mode_timer = time.ticks_ms()
        update_oled()
