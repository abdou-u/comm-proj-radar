from multiprocessing import Process, Queue
import subprocess
import os
import logging
import time
import queue
import sys
import scipy
import _thread
from scipy.signal import chirp
from scipy.io.wavfile import write
# import vlc

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from math import pi, sin, cos
from direct.interval.IntervalGlobal import Sequence
from direct.gui.OnscreenText import OnscreenText
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from prod_dca import producer_real_time_1843, producer_real_time_1843, producer_real_time_msense, phase_plot_len, freq_plot_len, range_plot_len, save_data_1843
import keyboard

def consumer(q, index):
    app = MyApp(q)
    app.run()


def main(exp_num,exp_object):

    num_producers = 1
    num_consumers = 1
    max_queue_size = 10000

    logging.info(f"Execution happening with {num_producers} producers and {num_consumers} consumers")

    q_main = Queue(maxsize=max_queue_size)

    producers = []
    consumers = []
    producers.append(Process(target=producer_real_time_1843, args=(q_main, 0)))

    
    # Create consumer processes
    for i in range(0, num_consumers):
        p = Process(target=consumer, args=(q_main, 0))
        p.daemon = False

        consumers.append(p)

    # Start the producers and consumer
    # The Python VM will launch new independent processes for each Process object
    for p in producers:
        p.start()
 
    for c in consumers:
        c.start()
 
    # Like threading, we have a join() method that synchronizes our program
    try:
        for p in producers:
            p.join()

        # Wait for empty chunks queue to exit
        for c in consumers:
            c.join()
    except KeyboardInterrupt as ki:
        print(f"Program terminated by keyboard")

    logging.info('Parent process exiting...')
    # update status to done, or cancelled or error?

class MyApp(ShowBase):
    def __init__(self, queue):
        ShowBase.__init__(self)

        self.q = queue
        # self.accept("escape", sys.exit, [0])

        #NEED TO CHANGE THESE EACH TIME
        self.fft_size = range_plot_len
        self.fft_range = [0, 1]
        self.phase_size = phase_plot_len
        self.phase_range = [-0.5, 0.5]
        self.freq_range = [0,1]
        self.freq_size = freq_plot_len #// 2# - 15# number of frames to show in the phase plot
        self.counter = 0
        self.start_time = 0
        self.starting_freq = 30
        self.playing = False
        self.remaining_time = 0

        # # self.buttons_al = "asdfghjklzx"
        # self.buttons = "qwertyuiopasdfghjklzxc12"
        # self.player = vlc.MediaPlayer("C:\\robotic-sensing\\OpenRadar\\test.mp3")

        # Create subplots for FFT and phase 
        plt.ion()
        self.fig = plt.figure()
        self.ax_fft = self.fig.add_subplot(211)
        # self.text_fft = self.ax_fft.text(0.56, 0.85, "", transform=self.ax_fft.transAxes, fontsize=15,verticalalignment='top', ha='left')
        # self.ax_phase = self.fig.add_subplot(211) 
        # self.ax_mrf = self.fig.add_subplot(212)
        # self.text_mrf = self.ax_mrf.text(0.56, 0.85, "", transform=self.ax_fft.transAxes, fontsize=15,verticalalignment='top', ha='left')
        #############################################
        self.ax_freq = self.fig.add_subplot(212)
        self.text_freq = self.ax_freq.text(0.90, 0.85, "Nothing" , fontsize=40, transform=self.ax_freq.transAxes, verticalalignment='top', ha='right')

        mng = plt.get_current_fig_manager()
        mng.window.state('zoomed') #works fine on Windows!

        # initialize FFT plot
        self.fft_x_data = np.arange(self.fft_size)
        self.fft_y_data = np.zeros_like(self.fft_x_data)
        self.line_fft = self.ax_fft.stem(self.fft_x_data, self.fft_y_data)
        # self.ax_fft.set_xticks(self.fft_x_data) 
        # self.ax_fft.set_xticklabels(np.arange(self.fft_size))
        self.ax_fft.set_ylim(self.fft_range)

        # self.mrf_x_data = np.arange(64)
        # self.mrf_y_data = np.zeros_like(self.mrf_x_data)
        # self.line_mrf, = self.ax_mrf.plot(self.mrf_x_data, self.mrf_y_data)
        # self.mrf_y_data_update = 0
        # self.ax_mrf.set_ylim(self.fft_range)

        # initialize phase plot
        # self.phase_x_data = np.arange(self.phase_size)
        # self.phase_y_data = np.zeros_like(self.phase_x_data)
        # self.phase_y_data_update = 0
        # self.line_phase, = self.ax_phase.plot(self.phase_x_data, self.phase_y_data)
        # self.ax_phase.set_ylim(self.phase_range)

        # initialize the freq spectrum plot
        self.freq_x_data = np.arange(self.freq_size)
        self.freq_y_data = np.zeros_like(self.freq_x_data)
        self.line_freq, = self.ax_freq.plot(self.freq_x_data, self.freq_y_data)
        self.ax_freq.set_ylim(self.freq_range)
        self.ax_freq.set_xticks(np.arange(0, self.freq_size , 20))
        # self.ax_freq.set_xticklabels(np.arange(15, self.freq_size + 15, 5))
        self.ax_freq.set_xticklabels(np.arange(0, self.freq_size, 20))

        self.taskMgr.add(self.updateDataTask, "updateDataTask")
        self.taskMgr.add(self.updateFFTPlotTask, "updateFFTPlotTask")
        # self.taskMgr.add(self.updateMRFPlotTask, "updateMRFPlotTask")
        # self.taskMgr.add(self.updatePhasePlotTask, "updatePhasePlotTask")
        ########################
        self.taskMgr.add(self.updateFreqPlotTask, "updateFreqPlotTask")
        self.taskMgr.add(self.playSoundTask, "playSoundTask")


    def play_sound(self, select, buttons):
        return
        # subprocess.call(["afplay", "C:\robotic-sensing\OpenRadar\chirp.wav"])
        # print("here")
        # choice = buttons.index(select)
        
        # self.sounds = sounds#np.concatenate((sounds, ['chirp', 'sheets', 'fast','faster','fastest','shorter_chirp','combined_sin']))
        # file = "C:\\robotic-sensing\\OpenRadar\\sounds\\single-tone\\" + self.sounds[choice] + ".mp3"
        # self.player = vlc.MediaPlayer(file)
        # time.sleep(1)
        # self.player.play()
        # curr_time = time.time()
        # print("starting chirp: " + str(curr_time))
        # print("key pressed is: " + select + "\nsound file is: " + self.sounds[choice])


    # play sound with pressing the key 'p'
    def playSoundTask(self, task):
        # self.play_sound
        buttons = "qwertyuiopasdfghjklzxcvbnm1234567890" #"asdfghjklzx"
        for elem in buttons:
            self.accept(elem, self.play_sound, [elem, buttons])
        return Task.cont

    def updateFFTPlotTask(self, task):
        # self.line_fft.set_ydata(self.fft_y_data)
        # self.update_stem(self.line_fft[0], self.line_fft[1], self.line_fft[2])
        self.line_fft[0].set_ydata(self.fft_y_data)
        self.line_fft[1].set_paths([np.array([[xx, 0], 
                                    [xx, yy]]) for (xx, yy) in zip(self.fft_x_data, self.fft_y_data)])
        # self.line_fft = self.ax_fft.stem(self.fft_x_data, self.fft_y_data)
        self.ax_fft.set_ylim([np.min(self.fft_y_data)-1, np.max(self.fft_y_data)+1])
        # max_amp = np.max(self.fft_y_data)
        max_ind = np.argmax(self.fft_y_data)
        # mrf = max_amp * (max_ind * range_res) / 8
        # self.text_fft.remove()
        # self.text_fft = self.ax_fft.text(0.56, 0.85, "max bin " + str(max_ind) + " power:" + str(np.sum(self.fft_y_data[6:9])**2), transform=self.ax_fft.transAxes, fontsize=15,verticalalignment='top', ha='left')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        return Task.cont

    def updateMRFPlotTask(self, task):
        self.line_mrf.set_ydata(self.mrf_y_data)
        self.ax_mrf.set_ylim([np.min(self.mrf_y_data)-1, np.max(self.mrf_y_data)+1])
        # max_amp = np.max(self.fft_y_data)
        # max_ind = np.argmax(self.fft_y_data)
        # mrf = max_amp * (max_ind * range_res) / 8
        self.text_mrf.remove()
        self.text_mrf = self.ax_mrf.text(0.56, 0.85, "MRF: " + str("{:,.2f}".format(self.mrf_y_data[63])), transform=self.ax_mrf.transAxes, fontsize=15,verticalalignment='top', ha='left')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        return Task.cont
    #     pass

    def updatePhasePlotTask(self, task):
        self.line_phase.set_ydata(self.phase_y_data)#np.concatenate((self.phase_y_data[1:phase_plot_len], np.array([self.phase_y_data_update])), axis=0))
        # print(self.phase_y_data[phase_plot_len-1], self.phase_y_data_update)
        self.ax_phase.set_ylim([np.min(self.phase_y_data)-0.1, np.max(self.phase_y_data)+0.1])
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        return Task.cont

    def updateFreqPlotTask(self, task):
        # print(self.freq_size)
        self.line_freq.set_ydata(self.freq_y_data)
        self.ax_freq.set_ylim([0,max(1e-5,np.max(self.freq_y_data[18:]))])#[0, 1])
        self.text_freq.remove()
        self.text_freq = self.ax_freq.text(0.95, 0.85, str(np.argmax(self.freq_y_data[20:])) , fontsize=40, transform=self.ax_freq.transAxes, verticalalignment='top', ha='right')

        # self.text_freq = self.ax_freq.text(0.95, 0.85, labeled_obj + " is vibrating at freq: " + str(detected_freq) , fontsize=40, transform=self.ax_freq.transAxes, verticalalignment='top', ha='right')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        return Task.cont

    def updateDataTask(self, task):
        try:
            while self.q.qsize() > 0:
                self.counter += 1
                # print(time.time()-self.start_time, self.counter)
                new_data = self.q.get(block=False)
                if new_data[0] == "mrf":
                    # self.fft_y_data = new_data[1]
                    self.mrf_y_data_update = new_data[1]
                    self.mrf_y_data = np.concatenate((self.mrf_y_data[1:64], np.array([self.mrf_y_data_update])), axis=0)
                elif new_data[0] == "fft":
                    self.fft_y_data = new_data[1]
                elif new_data[0] == "freq":
                    self.freq_y_data = new_data[1]
                elif new_data[0] == "phase":
                    self.phase_y_data_update = new_data[1]
                    self.phase_y_data = np.concatenate((self.phase_y_data[1:phase_plot_len], np.array([self.phase_y_data_update])), axis=0)
                
        except:
            return Task.cont

        return Task.cont

import subprocess


if __name__ == "__main__":
    exp_num = 0
    exp_object = "black metal"
    main(exp_num, exp_object)



