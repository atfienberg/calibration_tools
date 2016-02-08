import time
import u3

d = u3.U3()
#d.debug = True

spi_conf_temp = {
	"AutoCS": True,
	"DisableDirConfig": False,
	"SPIMode": 'C',
	"SPIClockFactor": 0,
	"CSPINNum": 14,
	"CLKPinNum": 8,
	"MISOPinNum": 15,
	"MOSIPinNum": 9
	}

spi_conf_pga = {
	"AutoCS": True,
	"DisableDirConfig": False,
	"SPIMode": 'C',
	"SPIClockFactor": 0,
	"CSPINNum": 11,
	"CLKPinNum": 8,
	"MISOPinNum": 10,
	"MOSIPinNum": 9
}

spi_conf_eeprom = {
	"AutoCS": True,
	"DisableDirConfig": False,
	"SPIMode": 'C',
	"SPIClockFactor": 0,
	"CSPINNum": 16,
	"CLKPinNum": 8,
	"MISOPinNum": 15,
	"MOSIPinNum": 9
}


def read_temperature():
	#make sure pga CS is high
	d.setDOState(spi_conf_pga['CSPINNum'], 1)
	d.setDOState(spi_conf_eeprom['CSPINNum'], 1)
	data = d.spi([0x50, 0x00, 0x00, 0x00], **spi_conf_temp)
	res = data['SPIBytes']
	temp = (res[1] << 8 | res[2]) / 128.0
	return temp

def setup_temperature():
	#make sure pga CS is high
	d.setDOState(spi_conf_pga['CSPINNum'], 1)
	d.setDOState(spi_conf_eeprom['CSPINNum'], 1)
	data = d.spi([0x08, 0x80], **spi_conf_temp)

def set_gain(gain_value):
	#make sure temp chip CS is high
	d.setDOState(spi_conf_temp['CSPINNum'], 1)
	d.setDOState(spi_conf_eeprom['CSPINNum'], 1)

        res = d.spi([0x83, 0x00], **spi_conf_pga)
	gain_read = res['SPIBytes'][1]
        print "old gain readout: %d = %f dB" % (gain_read, 26 - gain_read / 4.0)
        
        res = d.spi([0x03, gain_value], **spi_conf_pga)

        res = d.spi([0x83, 0x00], **spi_conf_pga)
	gain_read = res['SPIBytes'][1]
        print "new gain readout: %d = %f dB" % (gain_read, 26 - gain_read / 4.0)

if __name__ == "__main__":

	setup_temperature()
	set_gain(50)

	for i in range(10):
		time.sleep(1)
		print read_temperature()


