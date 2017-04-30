import os
import numpy as np
from mido import MidiFile
from midi_util import *

#Takes ORIGINAL path
def validate_data(path, quant):
    path_prefix, path_suffix = os.path.split(path)

    # Handle case where a trailing / requires two splits.
    if len(path_suffix) == 0:
        path_prefix, path_suffix = os.path.split(path_prefix)

    total_file_count = 0
    processed_count = 0

    base_path_out = os.path.join(path_prefix, path_suffix+'_valid')

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.split('.')[-1] == 'mid' or file.split('.')[-1] == 'MID':
                total_file_count += 1
                print 'Processing ' + str(file)
                midi_path = os.path.join(root,file)
                try:
                    midi_file = MidiFile(midi_path)
                except (KeyError, IOError, TypeError, IndexError, EOFError, ValueError):
                    print "Bad MIDI."
                    continue
                time_sig_msgs = [ msg for msg in midi_file.tracks[0] if msg.type == 'time_signature' ]

                if len(time_sig_msgs) == 1:
                    time_sig = time_sig_msgs[0]
                    if not (time_sig.numerator == 4 and time_sig.denominator == 4):
                        print '\tTime signature not 4/4. Skipping ...'
                        continue
                else:
                    # print time_sig_msgs
                    print '\tNo time signature. Skipping ...'
                    continue

                mid = quantize(MidiFile(os.path.join(root,file)), quant)
                if not mid:
                    print 'Invalid MIDI. Skipping...'
                    continue

                if not os.path.exists(base_path_out):
                    os.makedirs(base_path_out)

                out_file = os.path.join(base_path_out, file)

                print '\tSaving', out_file
                midi_file.save(out_file)
                processed_count += 1

    print '\nProcessed {} files out of {}'.format(processed_count, total_file_count)

#Takes VALID path
def quantize_data(path, quant):
    path_prefix, path_suffix = os.path.split(path)

    if len(path_suffix) == 0:
        path_prefix, path_suffix = os.path.split(path_prefix)

    total_file_count = 0
    processed_count = 0

    base_path_out = os.path.join(path_prefix, path_suffix+'_quantized')
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.split('.')[-1] == 'mid' or file.split('.')[-1] == 'MID':
                total_file_count += 1
                mid = quantize(MidiFile(os.path.join(root,file)),quant)
                if not mid:
                    print 'Invalid MIDI. Skipping...'
                    continue
                suffix = root.split(path)[-1]
                out_dir = base_path_out + '/' + suffix
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                out_file = os.path.join(out_dir, file)

                print 'Saving', out_file
                mid.save(out_file)

                processed_count += 1

    print 'Processed {} files out of {}'.format(processed_count, total_file_count)

#Takes QUANT path
def save_data(path, quant, one_hot=False):
    path_prefix, path_suffix = os.path.split(path)

    # Handle case where a trailing / requires two splits.
    if len(path_suffix) == 0:
        path_prefix, path_suffix = os.path.split(path_prefix)

    array_out = os.path.join(path_prefix, path_suffix+'_inputs')
    velocity_out = os.path.join(path_prefix, path_suffix+'_velocities')

    total_file_count = 0
    processed_count = 0

    for root, dirs, files in os.walk(path):
        for file in files:
            # print os.path.join(root, file)
            if file.split('.')[-1] == 'mid' or file.split('.')[-1] == 'MID':
                total_file_count += 1


                out_array = '{}.npy'.format(os.path.join(array_out, file))
                out_velocity = '{}.npy'.format(os.path.join(velocity_out, file))
                midi_path = os.path.join(root,file)
                midi_file = MidiFile(midi_path)

                print 'Processing ' + str(file)
                mid = MidiFile(os.path.join(root,file))

                # mid = quantize(midi_file,
                #                quantization=quant)

                if one_hot:
                    try:
                        array, velocity_array = midi_to_array_one_hot(mid, quant)
                    except (KeyError, TypeError, IOError, IndexError, EOFError, ValueError):
                        print "Out of bounds"
                        continue
                else:
                    array, velocity_array = midi_to_array(mid, quant)

                if not os.path.exists(array_out):
                    os.makedirs(array_out)

                if not os.path.exists(velocity_out):
                    os.makedirs(velocity_out)

                # print out_dir

                print 'Saving', out_array

                # print_array( mid, array)
                # raw_input("Press Enter to continue...")

                np.save(out_array, array)
                np.save(out_velocity, velocity_array)

                processed_count += 1
    print '\nProcessed {} files out of {}'.format(processed_count, total_file_count)

#Takes QUANT path
def load_data(path):
    names = []
    X_list = []
    Y_list = []
    path_prefix, path_suffix = os.path.split(path)

    # Handle case where a trailing / requires two splits.
    if len(path_suffix) == 0:
        path_prefix, path_suffix = os.path.split(path_prefix)

    x_path = os.path.join(path_prefix, path_suffix+"_inputs")
    y_path = os.path.join(path_prefix, path_suffix+"_labels")

    for filename in os.listdir(x_path):
        if filename.split('.')[-1] == 'npy':
            abs_path = os.path.join(x_path,filename)
            loaded = np.array(np.load(abs_path))


            X_list.append(loaded)

    for filename in os.listdir(y_path):
        if filename.split('.')[-1] == 'npy':
            abs_path = os.path.join(y_path,filename)
            loaded = np.array(np.load(abs_path))
            Y_list.append(loaded)

    # X_list = np.array(X_list)
    # Y_list = np.array(Y_list)


    return X_list, Y_list

def merge_results(orignal_path, quant_path, pred_path):

    path_prefix, path_suffix = os.path.split(orignal_path)

    # Handle case where a trailing / requires two splits.
    if len(path_suffix) == 0:
        path_prefix, path_suffix = os.path.split(path_prefix)

    file_names = []
    mids = []
    quant_mids = []
    velocities = []

    for root, dirs, files in os.walk(orignal_path):
        for file in files:
            if file.split('.')[-1] == 'mid' or file.split('.')[-1] == 'MID':
                midi_path = os.path.join(root, file)
                mid_file = MidiFile(midi_path)
                file_names.append(file)
                mids.append(mid_file)

    for root, dirs, files in os.walk(quant_path):
        for file in files:
            if file.split('.')[-1] == 'mid' or file.split('.')[-1] == 'MID':
                midi_path = os.path.join(root, file)
                mid_file = MidiFile(midi_path)
                quant_mids.append(mid_file)

    for root, dirs, files in os.walk(pred_path):
        for file in files:
            if file.split('.')[-1] == 'npy':
                vel_path = os.path.join(root, file)
                loaded = np.array(np.load(vel_path))
                velocities.append(loaded)

    styled_mids = []
    for i, file in enumerate(quant_mids):
        style_mid = stylify(file, velocities[i])
        styled_mids.append(style_mid)

    styled_out = os.path.join(path_prefix, path_suffix+"_styled_qmidi")

    if not os.path.exists(styled_out):
        os.makedirs(styled_out)

    for i, file in enumerate(styled_mids):
        out_file = os.path.join(styled_out, file_names[i])
        file.save(out_file)

    final_mids = []

    for i, file in enumerate(mids):
        final_mid = unquantize(file, styled_mids[i])
        final_mids.append(final_mid)

    final_out = os.path.join(path_prefix, path_suffix+"_final_midi")

    if not os.path.exists(final_out):
        os.makedirs(final_out)

    for i, file in enumerate(final_mids):
        out_file = os.path.join(final_out, file_names[i])
        file.save(out_file)

def create_final_midi(path):

    file_names = []
    mids = []
    quant_mids = []

    path_prefix, path_suffix = os.path.split(path)

    # Handle case where a trailing / requires two splits.
    if len(path_suffix) == 0:
        path_prefix, path_suffix = os.path.split(path_prefix)

    quant_path = os.path.join(path_prefix, path_suffix+"_quantized")

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.split('.')[-1] == 'mid' or file.split('.')[-1] == 'MID':
                midi_path = os.path.join(root, file)
                mid_file = MidiFile(midi_path)
                file_names.append(file)
                mids.append(mid_file)

    for root, dirs, files in os.walk(quant_path):
        for file in files:
            if file.split('.')[-1] == 'mid' or file.split('.')[-1] == 'MID':
                midi_path = os.path.join(root, file)
                mid_file = MidiFile(midi_path)
                quant_mids.append(mid_file)

    scrubbed_mids = []
    for file in quant_mids:
        scrub_mid = scrub(file,10)
        scrubbed_mids.append(scrub_mid)

    scrubbed_orig_mids = []
    for file in mids:
        scrub_mid = scrub(file,10)
        scrubbed_orig_mids.append(scrub_mid)

    scrubbed_out = os.path.join(path_prefix, path_suffix+"_clean_midi")

    if not os.path.exists(scrubbed_out):
        os.makedirs(scrubbed_out)
    #
    for i, file in enumerate(scrubbed_orig_mids):
        out_file = os.path.join(scrubbed_out, file_names[i])
        file.save(out_file)

    print "Bad MIDI. Header not found."

    _ , velocities = load_data(quant_path)

    styled_mids = []
    print velocities
    for i, file in enumerate(scrubbed_mids):
        print "Styling"
        print velocities[i]
        style_mid = stylify(file, velocities[i])
        styled_mids.append(style_mid)


    styled_out = os.path.join(path_prefix, path_suffix+"_styled_q_midi")

    if not os.path.exists(styled_out):
        os.makedirs(styled_out)

    for i, file in enumerate(styled_mids):
        out_file = os.path.join(styled_out, file_names[i])
        file.save(out_file)

    final_mids = []

    for i, file in enumerate(scrubbed_orig_mids):
        final_mid = unquantize(file, styled_mids[i])
        final_mids.append(final_mid)

    final_out = os.path.join(path_prefix, path_suffix+"_final_midi")

    if not os.path.exists(final_out):
        os.makedirs(final_out)

    for i, file in enumerate(final_mids):
        out_file = os.path.join(final_out, file_names[i])
        file.save(out_file)


# save_data("./midi/evaluation_train_quantized", 4)
# save_data("./midi/evaluation_test_quantized", 4)

# create_final_midi("/Users/Iman/research/programs/style/midi/formatted_valid")
# validate_data("../../midi/live_formatted", 4)
# validate_data("./midi/formatted_valid", 4)
# quantize_data("../../midi/classical", 4)
# save_data("../../midi/classical_quantized", 4, one_hot=True)

# x, y = load_data("./midi/formatted_valid_quantized")
#
# import matplotlib.pyplot as plt
#
# fig = plt.figure()
#
# fig.add_subplot(2,2,1)
# plt.imshow(x[-3])
#
# fig.add_subplot(2,2,2)
# plt.imshow(y[-3])
# plt.show()