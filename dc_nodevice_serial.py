from machine import Pin
import time
import os

input_button_pins = [28, 27, 26, 22, 20, 23, 21, 2]
input_buttons = [Pin(pin, Pin.IN, Pin.PULL_UP) for pin in input_button_pins]

led_onboard = machine.Pin(17, machine.Pin.OUT)

def load_state():
    global coin_inserted, coin_dispensed, button3_count, button4_count, button5_count, now_game_count, sec, door
    sec = False
    door = False
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
    
def save_state():
    global last_saved_values
    current_state = (coin_inserted, coin_dispensed, button3_count, button4_count, button5_count, now_game_count)
    if current_state != last_saved_values:
        with open("state.txt", "w") as f:
            f.write(f"{coin_inserted},{coin_dispensed},{button3_count},{button4_count},{button5_count},{now_game_count}")
        last_saved_values = current_state
        
load_state()
last_saved_values = (coin_inserted, coin_dispensed, button3_count, button4_count, button5_count, now_game_count)

last_save_time = time.ticks_ms()
prev_state = None

def handle_interrupt(pin):
    global coin_inserted, coin_dispensed, button3_count, button4_count, button5_count, now_game_count, sec, door, prev_state
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
            #now_game_count = 0 
        elif pin_index == 7:  
            reset_state()
        elif pin_index == 1:
            sec = True
        elif pin_index == 0:
            door = True
    else:
        if pin_index == 4:
            now_game_count = 0
        elif pin_index == 3:
            now_game_count = 0
        elif pin_index == 2:
            now_game_count = 0
        elif pin_index == 1:
            sec = False
        elif pin_index == 0:
            door = False
            
    current_state = (coin_inserted, coin_dispensed, button3_count, button4_count, button5_count, now_game_count, sec, door)
    if current_state != prev_state:
        print(f"{','.join(map(str, current_state))}")
        prev_state = current_state
        

for button in input_buttons:
    button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=handle_interrupt)
    
    
print(f"{coin_inserted},{coin_dispensed},{button3_count},{button4_count},{button5_count},{now_game_count},{sec},{door}")

while True:
    led_onboard.toggle()
    time.sleep(0.3)
    if time.ticks_diff(time.ticks_ms(), last_save_time) > 30000:
        save_state()
        last_save_time = time.ticks_ms()
