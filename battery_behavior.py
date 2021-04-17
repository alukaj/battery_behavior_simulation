import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
plt.style.use('ggplot')
from random import choices
import statistics
from scipy import stats

#Defining important variables
max_time = 20000
plots = 1000
time = np.linspace(0, max_time-1, num = max_time)
updated_devices = np.zeros(max_time)
pdf_x_values = (np.array(time)[:-1] + np.array(time)[1:]) / 2
max_time_plot_value = 0

#Customizable variables 
error_probability = 0.2
devices = 150
packets_needed = 100

packets_received = np.zeros([max_time, devices])
errors = [0, 1]
rate = [1-error_probability, error_probability]


#Defining error rate function, returns true if the packet is sent successfully, else false
def error_rate(errors, rate): 
    #Define the probability rate for receiving the packet or not
    if choices(errors, rate) == [0]:
        return True
    else:
        return False

#Defining the function to plot the pdf of the simulations
def find_density_function_for_simulation(max_time, time, simulations_completed, pdf_y_values):
    pdf_y_values = np.diff(simulations_completed)/ np.diff(time)
    return pdf_y_values

#Defining the function to find the mean with the 30th and 70th percentile       
def find_median_70thpercentile_30thpercentile(max_time, percentage_updated_devices):
    median_percentage_updated_devices = np.zeros(max_time)
    seventieth_percentile_percentage_updated_devices = np.zeros(max_time)
    thirtieth_percentile_percentage_updated_devices = np.zeros(max_time)
    for t in range (0, max_time):
        median_percentage_updated_devices[t] = statistics.median(percentage_updated_devices[:,t])
        thirtieth_percentile_percentage_updated_devices[t] = np.percentile(percentage_updated_devices[:,t], 30)
        seventieth_percentile_percentage_updated_devices[t] = np.percentile(percentage_updated_devices[:,t], 70)
    return median_percentage_updated_devices, thirtieth_percentile_percentage_updated_devices, seventieth_percentile_percentage_updated_devices
        
#Defining function to calculate simulations finished per each time      
def find_simulations_finished_for_each_timestamp(max_time, time, percentage_updated_devices, simulations_completed):
    for t in range(0, max_time):
        values = percentage_updated_devices[:,t][percentage_updated_devices[:,t]==1]
        simulations_completed[t] = len(values)
    
    #Finding the time when the first simulation is completed to plot a better visible graph
    for t in range(0, max_time):
        if simulations_completed[t] != 0:
            min_time_plotting = t
            break
    return simulations_completed, min_time_plotting

#Define function to find the data needed for plotting the histogram        
def plot_histogram(pdf_x_values, pdf_y_values, time, simulations_completed, min_time_plotting, max_time_plot_value):
    pdf_y_values = np.diff(simulations_completed)/ np.diff(time)
    bins = 50    
    #In order to define a reasonable number of bins, we should resize the elements of the x and y values
    new_x_values = pdf_x_values[int(min_time_plotting):int(max_time_plot_value)+1]
    new_y_values = pdf_y_values[int(min_time_plotting):int(max_time_plot_value)+1]
    
    bin_sum, bin_edges, binnumber = stats.binned_statistic(new_x_values, new_y_values, statistic='sum', bins=bins)
    bin_width = (bin_edges[1] - bin_edges[0])
    bin_centers = bin_edges[1:] - bin_width/2
    
    return bin_sum, bin_edges


#Define class for sending data via broadcast method
class Broadcast:
    def resulting_indexes(self, devices, current_packets_received, current_percentage_updated_devices, packets_needed): #Added additional variables which are not used for consistency
        self.devices_to_update = []
        for d in range (0, devices):
            self.devices_to_update.append(d)
        return self.devices_to_update
    
#Define class for sending data via broadcast method
class Unicast:
    def __init__(self):
        self.unicast_counter = 0
    def resulting_indexes(self, devices, current_packets_received, current_percentage_updated_devices, packets_needed): #Added additional variables which are not used for consistency
        devices_to_update = []
        devices_to_update.append(self.unicast_counter%devices)
        
        while current_packets_received[devices_to_update[0]] == packets_needed:
            self.unicast_counter = self.unicast_counter + 1
            devices_to_update[0] = self.unicast_counter%devices
        self.unicast_counter += 1
        return devices_to_update

#Define class to send data in broadcast up until 80% of the devices are done with the update, and then unicast
class CombinedMethods:
    def __init__(self):
        self.unicast_counter = 0
    def resulting_indexes(self, devices, current_packets_received, current_percentage_updated_devices, packets_needed):
        devices_to_update = []  
        if current_percentage_updated_devices<0.8:
            for d in range(0, devices):
                devices_to_update.append(d)           
        else:
            devices_to_update.append(self.unicast_counter%devices)
            while current_packets_received[devices_to_update[0]] == packets_needed:
                self.unicast_counter = self.unicast_counter + 1
                devices_to_update[0] = self.unicast_counter%devices
        
        self.unicast_counter += 1
        return devices_to_update

def get_percentage_updated_devices(plots, strategy, max_time, max_time_plotting, percentage_updated_devices, ticks_per_device, packets_needed):
    for k in range(0, plots):
        foo = strategy()
        for t in range (0, max_time):
            devices_to_update = foo.resulting_indexes(devices, packets_received[t], percentage_updated_devices[k][t-1], packets_needed)
            for d in devices_to_update:
                ticks_per_device[k][d] += 1
                if error_rate(errors, rate):
                    if packets_received[t][d]<packets_needed:
                        packets_received[t][d] += 1
            for d in range (0, devices):
                if packets_received[t][d] == packets_needed:
                    updated_devices[t] += 1
            if t<max_time-1:
                packets_received[t+1,:] = packets_received[t,:]
            percentage_updated_devices[k][t] = updated_devices[t]/devices
            if percentage_updated_devices[k][t] == 1:
                percentage_updated_devices[k][t:] = 1
                max_time_plot = t
                break    
        max_time_plotting[k] = max_time_plot #Variable needed to determine the time the slowest simulation took to run
        packets_received.fill(0)
        updated_devices.fill(0)
    return percentage_updated_devices, max_time_plotting, ticks_per_device 
    
#Define function to run the simulation and plot the needed graphs
def run_simulation(strategy1, strategy2, find_simulations_finished_for_each_timestamp, find_density_function_for_simulation, plot_histogram, find_median_70thpercentile_30thpercentile):
    global max_time_plot_value
    percentage_updated_devices = np.zeros([plots, max_time])
    max_time_plotting = np.zeros(plots)
    ticks_per_device = np.zeros([plots, devices]) 
    #Getting the percentage of devices finished for the first strategy
    percentage_updated_devices_first, max_time_plotting_first, ticks_per_device_first =  get_percentage_updated_devices(plots, strategy1, max_time, max_time_plotting, percentage_updated_devices, ticks_per_device, packets_needed)
    
    for k in range(0, plots):
        plt.plot(time, percentage_updated_devices_first[k,:])
    
    #Making the following variables zero to avoid overwriting
    percentage_updated_devices = np.zeros([plots, max_time])
    max_time_plotting = np.zeros(plots)
    ticks_per_device = np.zeros([plots, devices])
    
    #Getting the percentage of devices finished for the second strategy
    percentage_updated_devices_second, max_time_plotting_second, ticks_per_device_second = get_percentage_updated_devices(plots, strategy2, max_time, max_time_plotting, percentage_updated_devices, ticks_per_device, packets_needed)
    
    for k in range(0, plots):
        plt.plot(time, percentage_updated_devices_second[k,:])
    #percentage_updated_devices_3, max_time_plotting_3 = get_percentage_updated_devices(plots, strategy3, max_time)

    plt.rcParams['figure.figsize'] = [30, 20]
    plt.title('Percentage of devices that have completed the update over time for different simulations', fontsize = 26)
    max_time_plotting_concatenated = np.concatenate([max_time_plotting_first, max_time_plotting_second])
    max_time_plot_value = np.amax(max_time_plotting_concatenated)
    max_time_plot_value_first = np.amax(max_time_plotting_first)
    max_time_plot_value_second = np.amax(max_time_plotting_second)
    plt.xlim([0, max_time_plot_value])
    plt.xlabel('Time', fontsize = 20)
    plt.ylabel('Devices that completed the update', fontsize = 20)
    plt.show()
    
    #Plotting the simulations finished for each timestamp
    simulations_completed = np.zeros(max_time)
    simulations_completed_first, min_time_plotting_first = find_simulations_finished_for_each_timestamp(max_time, time, percentage_updated_devices_first, simulations_completed)
    simulations_completed = np.zeros(max_time)
    simulations_completed_second, min_time_plotting_second = find_simulations_finished_for_each_timestamp(max_time, time, percentage_updated_devices_second, simulations_completed)
   
    plt.plot(time, simulations_completed_first, label = 'Using CombinedMethods') 
    plt.plot(time, simulations_completed_second, label= 'Using Broadcast')

    plt.xlim([0, max_time_plot_value])
    plt.title('Simulations finished over time, devices =' +str(devices)+ ', packets needed to finish update = ' +str(packets_needed)+ ', error probability = ' +str(error_probability), fontsize=26)
    plt.xlabel('Time', fontsize = 20)
    plt.ylabel('Simulations finished', fontsize=20)
    plt.legend(fontsize = 20)
    plt.show()
    
    
    #Plotting the density function for the simulations finished per each timestamp
    pdf_y_values = np.zeros(max_time)
    pdf_y_values_first = find_density_function_for_simulation(max_time, time, simulations_completed_first, pdf_y_values)
    pdf_y_value = np.zeros(max_time)
    pdf_y_values_second = find_density_function_for_simulation(max_time, time, simulations_completed_second, pdf_y_values)
    plt.plot(pdf_x_values, pdf_y_values_first, label = 'Using CombinedMethods')
    plt.plot(pdf_x_values, pdf_y_values_second, label = 'Using Broadcast')
    plt.rcParams['figure.figsize'] = [30, 20]
    plt.title('Density functions for Simulations finished over time, devices =' +str(devices)+ ', packets needed to finish update = ' +str(packets_needed)+ ', error probability = ' +str(error_probability), fontsize = 26)
    plt.xlabel('Time', fontsize = 20)
    plt.ylabel('Probability Density Function')
    min_time_plotting = min(min_time_plotting_first, min_time_plotting_second)
    plt.xlim([min_time_plotting-10, max_time_plot_value+10])
    plt.legend(fontsize = 20)
    plt.show()
    
    #Plotting the histogram of simulations fineshed over time
    bin_sum_first, bin_edges_first = plot_histogram(pdf_x_values, pdf_y_values_first, time, simulations_completed_first, min_time_plotting, max_time_plot_value)
    bin_sum_second, bin_edges_second = plot_histogram(pdf_x_values, pdf_y_values_second, time, simulations_completed_second, min_time_plotting, max_time_plot_value)

    plt.hlines(bin_sum_first, bin_edges_first[:-1], bin_edges_first[1:], colors='g', lw=2, label = 'Using CombinedMethods')
    #Plotting vertical lines to make the graph look like a bar chart
    plt.vlines(bin_edges_first[:-1], 0, bin_sum_first, colors='g', lw=2)
    np.append(0, bin_edges_first)
    plt.vlines(bin_edges_first[1:], 0, bin_sum_first, colors='g', lw=2)
    
    plt.hlines(bin_sum_second, bin_edges_second[:-1], bin_edges_second[1:], colors='b', lw=2, label = 'Using Broadcast')
    #Plotting vertical lines to make the graph look like a bar chart
    plt.vlines(bin_edges_second[:-1], 0, bin_sum_second, colors='b', lw=2)
    np.append(0, bin_edges_second)
    plt.vlines(bin_edges_second[1:], 0, bin_sum_second, colors='b', lw=2)
    
    plt.title('Histogram of simulations finished over time, devices =' +str(devices)+ ', packets needed to finish update = ' +str(packets_needed)+ ', error probability = ' +str(error_probability), fontsize = 26)
    plt.xlabel('Time', fontsize = 20)
    plt.ylabel('Simulations finished in a specific time interval', fontsize = 20)
    plt.legend(fontsize = 20)
    plt.show()
    
    #Plotting the median, 30th and 70th percentile
    median_percentage_updated_devices_first, thirtieth_percentile_percentage_updated_devices_first, seventieth_percentile_percentage_updated_devices_first = find_median_70thpercentile_30thpercentile(max_time, percentage_updated_devices_first)
    median_percentage_updated_devices_second, thirtieth_percentile_percentage_updated_devices_second, seventieth_percentile_percentage_updated_devices_second = find_median_70thpercentile_30thpercentile(max_time, percentage_updated_devices_second)

    plt.plot(time, median_percentage_updated_devices_first, label='Median values for CombinedMethods')
    plt.plot(time, thirtieth_percentile_percentage_updated_devices_first)
    plt.plot(time, seventieth_percentile_percentage_updated_devices_first)
    plt.plot(time, median_percentage_updated_devices_second, label='Median values for Broadcast')
    plt.plot(time, thirtieth_percentile_percentage_updated_devices_second)
    plt.plot(time, seventieth_percentile_percentage_updated_devices_second)
    plt.title('Median, 30th and 70th percentile values in 3 different simulation plots, devices =' +str(devices)+ ', packets needed to finish update = ' +str(packets_needed)+ ', error probability = ' +str(error_probability), fontsize = 26)
    plt.xlabel('Time', fontsize = 20)
    plt.ylabel('Percentage of devices that have completed the update', fontsize = 20)
    plt.xlim([0, np.amax(max_time_plotting_first)])
    plt.legend(fontsize = 20)
    plt.show()
    
    #Plotting histogram for the ticks of the devices
    flattened_ticks_per_device_first = ticks_per_device_first.flatten()
    flattened_ticks_per_device_second = ticks_per_device_second.flatten()
    bins_first = int(max(flattened_ticks_per_device_first) - min(flattened_ticks_per_device_first))
    bins_second = int(max(flattened_ticks_per_device_second) - min(flattened_ticks_per_device_second))
    plt.hist(flattened_ticks_per_device_first, bins = bins_first, color = 'skyblue', histtype = u'step', lw = 5, label='Histogram for CombinedMethods')
    plt.hist(flattened_ticks_per_device_second, bins = bins_second, color = 'green', histtype = u'step', lw = 5, label='Histogram for Broadcast')
    plt.title('Histogram for the times the devices have been turned on until the end of the update, devices =' +str(devices)+ ', packets needed to finish update = ' +str(packets_needed)+ ', error probability = ' +str(error_probability), fontsize = 26)
    plt.xlabel('Number of ticks', fontsize = 20)
    plt.ylabel('Number of occurences for a specific interval of ticks', fontsize = 20)
    plt.legend(fontsize = 20) 
    plt.show()

#Line to call the function    
run_simulation(CombinedMethods, Broadcast, find_simulations_finished_for_each_timestamp, find_density_function_for_simulation, plot_histogram, find_median_70thpercentile_30thpercentile)