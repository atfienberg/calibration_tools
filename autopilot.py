import urllib
import urllib2
import re
import time
import sys
import serial
import subprocess
from itertools import product
import sipm_board

# events_per_run = 10000

# vga_setting = 50
# # bias_voltages = [str(66.7 + i*0.1) for i in xrange(4)]
# bias_voltages = ['68.5']
# filter_settings = ['1', '2', '3', '4', '5', '6', '1']
# # filter_settings = ['1']


def end_and_exit():
    """end run and exit if there's a problem"""
    urllib2.urlopen('http://localhost:5000/end')
    sys.exit(0)


def read_serial(s, terminator='\n'):
    """tries to read one byte at a time but breaks if timeout"""
    response = ''
    while True:
        old_len = len(response)
        try:
            response += s.read(1)
        except:
            continue
        try:
            if response[-1] == terminator:
                break
        except IndexError:
            # timed out
            break
        if len(response) == old_len:
            # timed out
            break
        response = response.strip()
    return response.strip()


def auto_run(bias_voltages, filter_settings, 
    vga_setting, events_per_run, comment):
    sipm_board.set_gain(vga_setting)
    filt_ser = serial.Serial('/dev/filterwheel', 115200, timeout=1)
    bias_ser = serial.Serial('/dev/keyspan', 4800, timeout=1)

    # make initial contact with bk and set current limit
    bias_ser.write('*IDN?\n')
    current_limit = 0.005
    bias_ser.write('SOUR:CURR % .4f\n' % current_limit)
    read_serial(bias_ser)
    bias_ser.write('SOUR:CURR?\n')
    response = read_serial(bias_ser)
    try:
        if float(response) != current_limit:
            print 'bk not workin. exiting'
            end_and_exit()
        else:
            print 'bias volt current limit %s' % response
    except:
        print 'bk not working. exiting'
        end_and_exit()
    bias_ser.write('OUTP:STAT 1\n')

    re_pattern = re.compile(r"^.*name='([\w \s]+)'.*value='(.*)'.*$")

    run_numbers = []
    processes = []

    for bias, setting in product(bias_voltages, filter_settings):
        # move filter wheel
        filt_ser.write('pos=%s\r' % setting)
        time.sleep(1)
        while True:
            message = read_serial(filt_ser, '>')
            if len(message) != 0 and message[-1] == '>':
                break

        filt_ser.write('pos?\r')
        message = read_serial(filt_ser, '>')
        read_setting = -1
        try:
            read_setting = int(message[-2])
        except ValueError:
            pass
        if repr(read_setting) != setting:
            print 'Error: filter wheel not moving properly.'
            end_and_exit()

        print 'filter wheel moved to setting %s' % setting

        # change bias
        if float(bias) > 70 or float(bias) < 0:
            print 'invalid bias setting: %s' % bias
            end_and_exit()            
        
        bias_ser.write('SOUR:VOLT %s\n' % bias)
        bias_ser.write('SOUR:VOLT?\n')
        if float(read_serial(bias_ser)) == float(bias):
            print 'bias changed successfully to %s' % bias
        else:
            'print bias failed to change'
            end_and_exit()

        new_page = urllib2.urlopen('http://localhost:5000/new')
        form_info = {}
        for l in new_page:
            words = l.split()
            if len(words) == 0:
                continue
            if words[0].strip() == "<thead><h3>Starting":
                run_numbers.append(words[2])
            match = re_pattern.search(l)
            if match != None:
                form_info[match.group(1)] = match.group(2)

        with open('temperatureFiles/labrun_%05i_temperature.txt'
                  % int(run_numbers[-1]), 'w') as f:
            form_info['Description'] = \
                'auto calibration\n filter setting %s: %s\n' % (
                setting, comment)

            temperature = sipm_board.read_temperature()
            form_info['Temperature'] = '%.2f' % temperature
            form_info['Bias Voltage'] = bias

            encdata = urllib.urlencode(form_info)

            # give bias a change to power up
            time.sleep(1)

            urllib2.urlopen('http://localhost:5000/start',
                            encdata)

            f.write('Event number, Temperature\n')
            f.write('0, %.2f\n' % temperature)

            while(True):
                time.sleep(1)
                n_events_page = urllib2.urlopen(
                    'http://localhost:5000/nEvents')
                n_events = int(n_events_page.next())
                temperature = sipm_board.read_temperature()
                f.write('%i, %.2f\n' % (n_events, temperature))
                if n_events > events_per_run:
                    break

            urllib2.urlopen('http://localhost:5000/end')

            print 'filter setting %s done, launching fitter' % setting

            processes.append(
                subprocess.Popen(
                    ["bash", "bin/crunchFiles.sh", run_numbers[-1]]))

    for process in processes:
        process.communicate()

    print 'all fits done!'

    run_list = []
    last_bias = None
    for (bias, setting), run in \
            zip(product(bias_voltages, filter_settings), run_numbers):
        if last_bias is None or bias != last_bias:
            run_list.append([float(bias),[]])
        run_list[-1][1].append(int(run))
        last_bias = bias
        print 'filter %s, bias %s : run %s' % (setting, bias, run)

    bias_ser.write('OUTP:STAT 0\n')
    time.sleep(1)

    bias_ser.close()
    filt_ser.close()

    return run_list
