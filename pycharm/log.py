# | Level | Numerical Value |
# | :-: | :-: |
# | CRITICAL | 50 |
# | ERROR | 40 |
# | WARNING | 30 |
# | INFO | 20 |
# | DEBUG | 10 |
# | NOTSET | 0 |

import os
import logging

class RollingLogger(object):
    """
    Rotary logger class. The log is stored in numerated files inside ./log/ folder. The number file will rotate
    until it reaches the max_log_files. log0000.log is always the last log.
    """
    
    def __init__(self, max_log_files):
        """ 
        Init the RollingLogger object.

        Parameters
        ----------
        max_log_files: Maximum quantity of files to store inside the log folder.
        """
        self.NUMBER_OF_LOGS = max_log_files
        self.LOG = self._logger_settings()

    def _logger_settings(self):
        """ 
        Function that configure the logger.
        
        Return
        ----------
        The logger object.
        """
        self._log_directory()
        logging.basicConfig(filename= self.path + self.filename, 
                            filemode='w', 
                            level=logging.INFO, 
                            format='%(asctime)s | Severity = %(levelname)s | Message = %(message)s')
        return logging.getLogger()

    def _log_directory(self):
        """ 
        Function that creates the folder, if it doesn't exist, and the corresponding log file.
        """
        self.path = 'logs/'

        if not os.path.exists(self.path):
            os.makedirs(self.path)
            self.filename = 'log0000.log'
        else:
            self.filename = self._get_next_log_file_name()

    def _get_next_log_file_name(self):
        """
        Function that searches for the existing logs and manges it's rotation.
        
        Return
        ----------
        The file name to be created and used to log.
        """
        file_digits_lst = []
        for filename in os.listdir(self.path):
            if "log" in filename.split(".")[-1]:
            #If it has the .log extension , searches for the digits.
                digits = ''
                for char in filename:
                    if char.isdigit():
                        digits += char
                file_digits_lst.append(int(digits))

        if not file_digits_lst:
        #Empty directory, creates the 1st log.
            return 'log0000.log'
        else:
        #The directory has files so we search for the last one.
            latest_file_number = max(file_digits_lst)
            if latest_file_number >= self.NUMBER_OF_LOGS - 1:
                #If existes a file with the higher possible numeration, it's deleted.
                largest_file_name = self.path + 'log' + '{0:04d}'.format(latest_file_number) + '.log'
                os.remove(largest_file_name)
            #Rolls the remaining files by +1 in there numeration.
            for i in range(self.NUMBER_OF_LOGS - 1, 0, -1):
                name1 = self.path + 'log' + '{0:04d}'.format(i - 1) + '.log'
                name2 = self.path + 'log' + '{0:04d}'.format(i) + '.log'
                if os.path.isfile(name1):
                    os.rename(name1, name2)
            return 'log0000.log'




