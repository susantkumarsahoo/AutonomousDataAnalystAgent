import sys
from datetime import datetime

# Control program behavior Represents a specific business or system failure Stops execution 
# Used to enforce rules and fail fastCan be mapped to API responses or workflows error file name and file line number easy to read error message  

class CustomException(Exception):
    """
    Custom exception class for handling project-level errors across
    ML/DL pipelines. Captures full traceback and provides a clear,
    structured error message format.

    Usage:
        raise ProjectException(e, sys)
    """

    def __init__(self, error_message: Exception, error_details: sys):
        """
        Creates a formatted exception containing contextual traceback information.

        Parameters
        ----------
        error_message : Exception
            The error that was raised.
        error_details : sys
            System object for extracting traceback details.
        """
        super().__init__(str(error_message))
        self.error_message = CustomException.get_detailed_error_message(
            error_message,
            error_details
        )

    @staticmethod
    def get_detailed_error_message(error_message: Exception, error_details: sys) -> str:
        """
        Extracts line number, file name, and error information.

        Returns
        -------
        str
            Formatted detailed exception string.
        """
        _, _, exc_tb = error_details.exc_info()

        file_name = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return (
            "\n" + "=" * 70 +
            f"\nTimestamp     : {timestamp}"
            f"\nFile Name     : {file_name}"
            f"\nLine Number   : {line_number}"
            f"\nError Message : {str(error_message)}"
            "\n" + "=" * 70 + "\n"
        )

    def __str__(self):
        return self.error_message

  
'''

try:
    x = undefined_variable
except Exception as e:
    logger.error(str(CustomException(e, sys)))

'''

