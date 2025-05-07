from machine import Pin, Timer, SoftI2C, ADC, PWM
from time import sleep, time
import ssd1306, utime

# Initialize I2C for OLED
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Initialize Button with Pull-Up resistor (active low)
button = Pin(14, Pin.IN, Pin.PULL_UP)

# Setup LED on Pin 2 (on-board LED for ESP32)
led = PWM(Pin(2), freq=1000)  # PWM frequency at 1kHz

# Setup Speaker on Pin 25 (on-board speaker for ESP32)
speaker = PWM(Pin(25), freq=1000)  # Initial PWM frequency for Speaker

# Potentiometer for Volume Control
potentiometer = ADC(Pin(34))  # Assuming Pin 34 is used for Potentiometer
potentiometer.width(ADC.WIDTH_10BIT)  # 10-bit resolution (0-1023)
potentiometer.atten(ADC.ATTN_11DB)  # Full range (0 - 3.3V)

# Global variable for mode tracking
current_mode = 0  # Start in Mode Selection (Mode 0)
button_press_count = 0  # Counter for button presses
is_holding_button = False  # Track if button is being held

# Timer for button hold check
#hold_timer = Timer(0)  # Assign Timer 0
# timer active too slow for change mode2-->mode1, using time instead 

#set duration of note
SEC_IN_uSEC = 1000000
#set frequency of each note
NOTE_FREQ_C = 261.63  # Frequency of note C in Hz
NOTE_FREQ_D = 293.66  # Frequency of note D in Hz
NOTE_FREQ_E = 329.63  # Frequency of note E in Hz
NOTE_FREQ_F = 349.23  # Frequency of note F in Hz
NOTE_FREQ_G = 392.00  # Frequency of note G in Hz
NOTE_FREQ_A = 440.00  # Frequency of note A in Hz
NOTE_FREQ_B = 246.94  # Frequency of note B in Hz

song1 = [
    (NOTE_FREQ_A, SEC_IN_uSEC // 2),  #A
    (NOTE_FREQ_B, SEC_IN_uSEC // 2),  #B 
    (NOTE_FREQ_C, SEC_IN_uSEC // 2),  #C
    (NOTE_FREQ_D, SEC_IN_uSEC // 2),  #D
    (NOTE_FREQ_C, SEC_IN_uSEC // 6),  #E
    (NOTE_FREQ_E, SEC_IN_uSEC // 6),  #F
    (NOTE_FREQ_F, SEC_IN_uSEC // 6),  #G 
]

#test sound of speaker
def test_speaker():
    speaker.freq(1000)  # set frequency 1000 Hz
    speaker.duty(512)   # set duty cycle  50% (512 from 1023)
    sleep(1)            # let speaker sound for 1 sec
    speaker.duty(0)     # shut down speaker

# Function to display the current mode on OLED
def display_mode(mode):
    oled.fill(0)  # Clear screen
    if mode == 0:
        oled.text("Mode Selection", 0, 0)
        oled.text("1: Volume Control", 0, 20)
        oled.text("2: Game Mode", 0, 40)
    elif mode == 1:
        oled.text("Mode 1: Volume", 0, 0)
        oled.text("Adjusting Volume...", 0, 20)
    elif mode == 2:
        oled.text("Mode 2: Game", 0, 0)
        oled.text("Playing Game...", 0, 20)
    oled.show()

# Interrupt handler function for button
def handle_button_interrupt(pin):
    global current_mode, button_press_count, is_holding_button
    sleep(0.2)  # Debounce delay (200 ms)
    if pin.value() == 0 and not is_holding_button:  # If the button is still pressed (active low)
        button_press_count += 1  # Increment button press count
        
        if button_press_count == 1:
            current_mode = 1  # Go to Mode 1 (Volume Control)
        elif button_press_count == 2:
            current_mode = 2  # Go to Mode 2 (Game Mode)
            speaker.duty(0) 
        elif button_press_count >= 3:
            current_mode = 2  # Stay in Mode 2 after the 3rd press and onward
            speaker.duty(0) 
        
        display_mode(current_mode)  # Update the OLED with the current mode

# Attach interrupt to the button
button.irq(trigger=Pin.IRQ_FALLING, handler=handle_button_interrupt)

# Function for Adjusting Volume using Potentiometer, controlling LED brightness, and Speaker
def adjusting_volume(oled):
    # Read potentiometer value (0-1023)
    pot_value = potentiometer.read()
    global volume_percentage
    # Convert the value to percentage (0-100%)
    volume_percentage = int(pot_value / 1023 * 100)
    
    # Display volume level on OLED
    oled.fill(0)  # Clear screen
    oled.text("Mode 1: Volume", 0, 0)
    oled.text("Volume: {}%".format(volume_percentage), 0, 20)
    oled.show()

    # Control LED brightness based on volume level
    led.duty(int(volume_percentage * 1023 / 100))  # Set PWM duty cycle (0-1023 for ESP32)
    
    # Control Speaker frequency and volume based on Potentiometer
    speaker.duty(int(volume_percentage * 1023 / 100))  # Set PWM duty cycle for speaker
    speaker.freq(200 + int(volume_percentage * 5))  # Adjust frequency of speaker (200-700 Hz)
    
#functions play song 
def play_song(frequency,duration):
    speaker.freq(int(frequency))  # Set the frequency for the PWM
    if frequency == NOTE_FREQ_A:
        speaker.duty(int(volume_percentage * 1023 / 100))   # Set the duty cycle (0-1023, 900,100 sound stable)
    elif frequency == NOTE_FREQ_B:
        speaker.duty(int(volume_percentage * 900 / 100)) 
    elif frequency == NOTE_FREQ_C:
        speaker.duty(int(volume_percentage * 1023 / 100)) 
    elif frequency == NOTE_FREQ_D:
        speaker.duty(int(volume_percentage * 1023 / 100)) 
    elif frequency == NOTE_FREQ_E:
        speaker.duty(int(volume_percentage * 1023 / 100)) 
    elif frequency == NOTE_FREQ_F:
        speaker.duty(int(volume_percentage * 1023 / 100)) 
    elif frequency == NOTE_FREQ_G:
        speaker.duty(int(volume_percentage * 1023 / 100)) 
    utime.sleep_us(duration)  # Play the note for the specified duration
    speaker.duty(0)  # Turn off the sound after the note ends


# Timer callback function to reset to Mode 0 after 5 seconds hold
def reset_to_mode_0(t):
    global current_mode, button_press_count, is_holding_button
    print('resetting to mode0')
    current_mode = 0  # Reset to Mode 0
    button_press_count = 0  # Reset button press count
    is_holding_button = False  # Stop holding button
    display_mode(current_mode)

# Timer callback function to reset to Mode 0 after 5 seconds hold
def game_count():
    count = 0
    start_time = time()  # Get current time
    end_time = start_time + 7  # Countdown duration of 7 seconds
    while time() < end_time:
        if not button.value():  # Check for button press
            count += 1
            while not button.value():  # Wait for button release
                pass
        sleep(0.1)  # Prevent double counting
    # Display countdown and button press count
        remaining_time = int(end_time - time())
        oled.fill(0)  # Clear screen
        oled.text("Time: {}".format(remaining_time), 0, 0)
        oled.text("Count: {}".format(count), 0, 20)
        oled.show()
        sleep(0.1)  # Update display every 0.1 seconds
        
    # Show result
    if count >= 3:
        oled.fill(0)  # Clear screen again
        oled.text("WIN!!", 0, 0)
        oled.show()
    else:
        oled.fill(0)  # Clear screen again
        oled.text("YOU LOSE", 0, 0)
        oled.show()
        
    sleep(2)  # Show result for 2 seconds       
    oled.fill(0)  # Clear screen again

# display the mode0
display_mode(current_mode)  # Display the initial mode selection screen

# Test the speaker (call Speaker)
test_speaker()  # Test the speaker at the beginning of the program.

# Variables to track button hold time
hold_start_time = None

#set value of running game
game_has_run = False

# Main program loop
while True:
    if current_mode == 1:
        adjusting_volume(oled)  # Adjust volume in Mode 1
        for note, duration in song1:
            play_song(note, duration)
            utime.sleep(0.1)  # Short pause between notes
    elif current_mode == 2 and not game_has_run:  # Check if the game has not run yet
        game_count()  # Run the game
        game_has_run = True  # Set the flag indicating the game has run

    if button.value() == 0:  # If the button is pressed
        if hold_start_time is None:
            hold_start_time = time()  # Start timing
        elif time() - hold_start_time >= 5:  # Check if held for 5 seconds
            print("Button held for 5 seconds; resetting to Mode 0")  # Debug print
            current_mode = 0  # Reset to Mode 0
            button_press_count = 0
            display_mode(current_mode)
            hold_start_time = None  # Reset hold time
    else:
        hold_start_time = None  # Reset hold timer if button is released

    # Optionally reset the game state when going back to Mode 0
    if current_mode == 0:
        game_has_run = False  # Allow the game to run again next time
