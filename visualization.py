import matplotlib.pyplot as plt
import os

class Visualization:
    def __init__(self, path, dpi):
            self._path = path
            self._dpi = dpi


    def save_data_and_plot(self, data, filename, xlabel, ylabel):
        """
        Produce a plot of performance of the agent over the session and save the relative data to txt
        """
        min_val = min(data)
        max_val = max(data)

        plt.rcParams.update({'font.size': 24})  # set bigger font size

        plt.plot(data)
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.margins(0)
        plt.ylim(min_val - 0.05 * abs(min_val), max_val + 0.05 * abs(max_val))
        fig = plt.gcf()
        fig.set_size_inches(20, 11.25)
        fig.savefig(os.path.join(self._path, 'plot_'+filename+'.png'), dpi=self._dpi)
        plt.close("all")

        with open(os.path.join(self._path, 'plot_'+filename + '_data.txt'), "w") as file:
            for value in data:
                    file.write("%s\n" % value)

    def save_data(self, data, filename):
        """
            Save any data related to the training to a txt file   
        """
        with open(os.path.join(self._path, filename + '.txt'), "w") as file:
             file.write(str(data))
            # for key, value in data.items():
            #     if isinstance(value, (list, tuple)):
            #         file.write(f"{key}:\n")
            #         for i, item in enumerate(value, 1):
            #             file.write(f"  {i}. {item}\n")
            #     else:
            #         file.write(f"{key}: {value}\n")
          
    def overlayed_plot(self, fixed_time_data, model_data, filename, xlabel, ylabel):
        """
        Produce an overlayed plot of two datasets and save the relative data to txt
        """
        # Plot each with its own x-axis length
        plt.figure(figsize=(20, 5))
        plt.plot(range(len(fixed_time_data)), fixed_time_data, label=f'Fixed Time {ylabel}', marker='o')
        plt.plot(range(len(model_data)), model_data, label=f'Model {ylabel}', marker='s')
        plt.axhline(0, color='gray', linestyle='--')
        plt.title(f"{ylabel} Comparison")
        plt.xlabel(xlabel)
        plt.ylabel(f"{ylabel}")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        fig = plt.gcf()
        fig.savefig(os.path.join(self._path, 'plot_'+filename+'.png'), dpi=self._dpi)
        plt.close("all")