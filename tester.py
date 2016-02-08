from run_lists import run_number_list
from bias_scan import make_summary_plot

def main():
	new_list = [i for i in run_number_list if i[0] != 66.9]
	make_summary_plot(new_list, attr='sipm.threeSampleAmpl')

if __name__ == '__main__':
	main()
