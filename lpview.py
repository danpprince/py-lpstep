from Queue import Queue
import rtmidi.midiutil as midiutil
from threading import Thread

import notestates
import sequencermodel

# Get outputs that contain the string 'Launchpad'
lp_midi_out, midi_out_name = midiutil.open_midiport(port='Launchpad', type_='output')
print('Opening port \'{0}\' for output'.format(midi_out_name))

# Create note thread for sending notes generated by the sequencers 
# to prevent timing errors
note_queue = Queue()
def send_note(queue):
    while True:
        midi_message = queue.get()
        lp_midi_out.send_message(midi_message)

note_thread = Thread(target=send_note, args=(note_queue,))
note_thread.daemon = True
note_thread.start()

class GlobalLpView(object):
    def __init__(self, input_velocity):
        self.display_velocity(input_velocity)
        self.display_page(0)

    def display_velocity(self, velocity):
        # Use the up and down arrow buttons to indicate velocity
        vel_bit_1_button_cc = 104
        vel_bit_0_button_cc = 105

        if velocity == notestates.NOTE_VEL_LOW:
            note_queue.put([176, vel_bit_1_button_cc,  0])
            note_queue.put([176, vel_bit_0_button_cc, 48])
        else:
            note_queue.put([176, vel_bit_1_button_cc, 48])
            note_queue.put([176, vel_bit_0_button_cc,  0])

    def display_playing(self, state):
        # Use the right arrow button to toggle playing
        playing_button_cc = 107
        if state:
            note_queue.put([176, playing_button_cc, 48])
        else:
            note_queue.put([176, playing_button_cc,  0])

    def display_page(self, page_num):
        # Use the right arrow button to toggle playing
        user1_button_cc = 109
        user2_button_cc = 110
        if page_num == 0:
            note_queue.put([176, user1_button_cc, 48])
            note_queue.put([176, user2_button_cc,  0])
        else:
            note_queue.put([176, user1_button_cc,  0])
            note_queue.put([176, user2_button_cc, 48])

    def display_randomize(self, state):
        # Use the mixer button to toggle randomization of steps
        randomize_button_cc = 111
        if state:
            note_queue.put([176, randomize_button_cc, 48])
        else:
            note_queue.put([176, randomize_button_cc,  0])

class LpView(object):
    next_seq_even = False

    def __init__(self, rows):
        self.rows = rows
        self.clear()

        # Use the next_seq_even class variable in order to alternate colors
        # between sequences to improve clarity for users
        self.even_seq = LpView.next_seq_even
        LpView.next_seq_even = not LpView.next_seq_even

    def update(self, step, state):
        step_row = step / 8
        step_col = step % 8

        note_num = step_row*16 + step_col

        if state == notestates.NOTE_PLAYING:
            note_queue.put([144, note_num, 3 << 4])
        elif state == notestates.NOTE_VEL_HIGH:
            # Alternate the color for active steps between sequences
            if self.even_seq:
                green = 3
                red   = 2
                note_queue.put([144, note_num, (green << 4) + red])
            else:
                green = 2
                red   = 3
                note_queue.put([144, note_num, (green << 4) + red])
        elif state == notestates.NOTE_VEL_LOW:
            # Alternate the color for active steps between sequences
            if self.even_seq:
                green = 2
                red   = 1
                note_queue.put([144, note_num, (green << 4) + red])
            else:
                green = 1
                red   = 2
                note_queue.put([144, note_num, (green << 4) + red])
        elif state == notestates.NOTE_MUTED_LOW:
            note_queue.put([144, note_num,  1])
        elif state == notestates.NOTE_MUTED_HIGH:
            note_queue.put([144, note_num,  3])
        else:
            note_queue.put([144, note_num,  0])

    def mute_display(self, state, rows):
        if len(rows) == 2:
            for row in range(rows[0], rows[1]+1):
                step_col = 8
                note_num = row*16 + step_col

                if state:
                    note_queue.put([144, note_num, 13])
                else:
                    note_queue.put([144, note_num, 0])

        elif len(rows) == 1:
            step_col = 8
            note_num = rows[0]*16 + step_col

            if state:
                note_queue.put([144, note_num, 13])
            else:
                note_queue.put([144, note_num, 0])

    def clear(self):
        # All LEDs are turned off, and the mapping mode, buffer settings, and 
        # duty cycle are reset to their default values. 
        note_queue.put([176, 0, 0])
