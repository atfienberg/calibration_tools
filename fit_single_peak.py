from gain_calibration import fit_distribution
import sys

if __name__ == '__main__':
	if len(sys.argv) > 2:
		fit_distribution(int(sys.argv[1]), attr=str(sys.argv[2]), draw=True)
	elif len(sys.argv) > 1:
		fit_distribution(int(sys.argv[1]), draw=True)
	else:
		fit_distribution(1733, draw=True)
