import streamlit as st
import csv
import os
import struct
from pathlib import Path
import json
from typing import List, Dict, Optional, Union, Callable, Any, Iterator
import tempfile
import logging
from datetime import datetime, date
import traceback
import hashlib
import time  # For simulating delays/retries if needed, and for timing operations
import filelock # For cross-platform file locking




# Configure logging
logging.basicConfig(
    level=logging.INFO, # Set to logging.DEBUG to see detailed date parsing attempts
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('traffic_accidents.log'), # Log to a file
        logging.StreamHandler() # Also log to console
    ]
)
logger = logging.getLogger(__name__)

# --- Data Fields ---
# Define all fields for the DataObject and their expected types/validation rules
FIELDS = [
    'crash_date', 'traffic_control_device', 'weather_condition', 
    'lighting_condition', 'first_crash_type', 'trafficway_type',
    'alignment', 'roadway_surface_cond', 'road_defect', 'crash_type',
    'intersection_related_i', 'damage', 'prim_contributory_cause',
    'num_units', 'most_severe_injury', 'injuries_total', 'injuries_fatal',
    'injuries_incapacitating', 'injuries_non_incapacitating',
    'injuries_reported_not_evident', 'injuries_no_indication',
    'crash_hour', 'crash_day_of_week', 'crash_month'
]

# --- Custom Exceptions ---
class DataValidationError(Exception):
    """Custom exception for data validation errors within DataObject."""
    pass

class DatabaseError(Exception):
    """Custom exception for database operations and file I/O errors."""
    pass

class FileLockError(Exception):
    """Custom exception for errors acquiring/releasing file locks."""
    pass

# --- DataObject Class ---
class DataObject:
    """
    Represents a traffic accident record with enhanced validation and serialization.
    Each instance corresponds to a single record in the database.
    """
    
    def __init__(self, row_data: Optional[List[str]] = None, existing_data_dict: Optional[Dict[str, Any]] = None):
        """
        Initializes a DataObject.
        Can be initialized from a list of row data (e.g., from CSV) or an existing dictionary.
        """
        # Initialize all fields with type-appropriate default values
        self._initialize_defaults()
        
        if row_data is not None:
            try:
                self._initialize_from_row(row_data)
            except (DataValidationError, ValueError) as e:
                logger.error(f"Error initializing DataObject from row: {str(e)} | Row: {row_data}")
                raise DataValidationError(f"Invalid data for record: {str(e)}")
        elif existing_data_dict is not None:
            try:
                self._initialize_from_dict(existing_data_dict)
            except (DataValidationError, ValueError) as e:
                logger.error(f"Error initializing DataObject from dict: {str(e)} | Dict: {existing_data_dict}")
                raise DataValidationError(f"Invalid data for record: {str(e)}")

        # Perform comprehensive validation after initialization
        if not self.validate():
            raise DataValidationError("Data validation failed after initialization.")


    def _initialize_defaults(self):
        """Initializes all fields with safe and type-appropriate default values."""
        self.crash_date = ""
        self.traffic_control_device = "UNKNOWN"
        self.weather_condition = "UNKNOWN"
        self.lighting_condition = "UNKNOWN"
        self.first_crash_type = "UNKNOWN"
        self.trafficway_type = "UNKNOWN"
        self.alignment = "UNKNOWN"
        self.roadway_surface_cond = "UNKNOWN"
        self.road_defect = "NONE"
        self.crash_type = "UNKNOWN"
        self.intersection_related_i = "NO"
        self.damage = "UNKNOWN"
        self.prim_contributory_cause = "UNKNOWN"
        self.num_units = 0
        self.most_severe_injury = "NONE"
        self.injuries_total = 0.0
        self.injuries_fatal = 0.0
        self.injuries_incapacitating = 0.0
        self.injuries_non_incapacitating = 0.0
        self.injuries_reported_not_evident = 0.0
        self.injuries_no_indication = 0.0
        self.crash_hour = 0
        self.crash_day_of_week = 1 # Monday
        self.crash_month = 1      # January

    def _initialize_from_row(self, row_data: List[str]):
        """
        Populates object fields from a list of strings (e.g., from a CSV row).
        Performs basic type conversion and uses validation helpers.
        """
        if len(row_data) != len(FIELDS):
            raise ValueError(f"Expected {len(FIELDS)} fields, but got {len(row_data)}.")
        
        # Processed data: strip whitespace and convert empty strings to None
        processed_data = [value.strip() if isinstance(value, str) else None for value in row_data]
        
        self.crash_date = self._validate_date(processed_data[0])
        self.traffic_control_device = self._validate_string(processed_data[1], "traffic_control_device", allow_empty=True)
        self.weather_condition = self._validate_string(processed_data[2], "weather_condition", allow_empty=True)
        self.lighting_condition = self._validate_string(processed_data[3], "lighting_condition", allow_empty=True)
        self.first_crash_type = self._validate_string(processed_data[4], "first_crash_type", allow_empty=True)
        self.trafficway_type = self._validate_string(processed_data[5], "trafficway_type", allow_empty=True)
        self.alignment = self._validate_string(processed_data[6], "alignment", allow_empty=True)
        self.roadway_surface_cond = self._validate_string(processed_data[7], "roadway_surface_cond", allow_empty=True)
        self.road_defect = self._validate_string(processed_data[8], "road_defect", allow_empty=True)
        self.crash_type = self._validate_string(processed_data[9], "crash_type", allow_empty=False) # Required field
        self.intersection_related_i = self._validate_yes_no(processed_data[10])
        self.damage = self._validate_string(processed_data[11], "damage", allow_empty=True)
        self.prim_contributory_cause = self._validate_string(processed_data[12], "prim_contributory_cause", allow_empty=True)
        self.num_units = self._validate_positive_int(processed_data[13], "num_units", min_val=0)
        self.most_severe_injury = self._validate_string(processed_data[14], "most_severe_injury", allow_empty=True)
        self.injuries_total = self._validate_positive_float(processed_data[15], "injuries_total", min_val=0.0)
        self.injuries_fatal = self._validate_positive_float(processed_data[16], "injuries_fatal", min_val=0.0)
        self.injuries_incapacitating = self._validate_positive_float(processed_data[17], "injuries_incapacitating", min_val=0.0)
        self.injuries_non_incapacitating = self._validate_positive_float(processed_data[18], "injuries_non_incapacitating", min_val=0.0)
        self.injuries_reported_not_evident = self._validate_positive_float(processed_data[19], "injuries_reported_not_evident", min_val=0.0)
        self.injuries_no_indication = self._validate_positive_float(processed_data[20], "injuries_no_indication", min_val=0.0)
        self.crash_hour = self._validate_range(processed_data[21], "crash_hour", 0, 23)
        self.crash_day_of_week = self._validate_range(processed_data[22], "crash_day_of_week", 1, 7) # 1=Monday, 7=Sunday
        self.crash_month = self._validate_range(processed_data[23], "crash_month", 1, 12)

    def _initialize_from_dict(self, data_dict: Dict[str, Any]):
        """
        Populates object fields from a dictionary (e.g., from JSON deserialization).
        Assumes dictionary keys match field names.
        """
        for field in FIELDS:
            if field in data_dict:
                # Direct assignment for most fields, validation happens in .validate()
                # Special handling for date, numbers where type conversion is needed
                if field == 'crash_date':
                    self.crash_date = self._validate_date(data_dict[field])
                elif field in ['num_units', 'crash_hour', 'crash_day_of_week', 'crash_month']:
                    setattr(self, field, self._validate_positive_int(str(data_dict[field]), field))
                elif field.startswith('injuries_') and field != 'injuries_no_indication': # All injury fields are floats
                    setattr(self, field, self._validate_positive_float(str(data_dict[field]), field))
                elif field == 'injuries_no_indication': # This one also float
                     setattr(self, field, self._validate_positive_float(str(data_dict[field]), field))
                elif field == 'intersection_related_i':
                    self.intersection_related_i = self._validate_yes_no(data_dict[field])
                else:
                    setattr(self, field, self._validate_string(data_dict[field], field, allow_empty=True))
            else:
                logger.warning(f"Field '{field}' missing in provided dictionary for DataObject initialization. Using default.")
                # Default values already set by _initialize_defaults


    @staticmethod
    def _validate_date(date_str: Optional[str]) -> str:
        """
        Validates and standardizes a date string to APAC-MM-DD format.
        Handles various common input formats including those with time and AM/PM.
        Raises DataValidationError if a non-empty string cannot be parsed.
        """
        logger.debug(f"[_validate_date] Input date_str: '{date_str}' ({type(date_str)})")
        if not date_str:
            logger.debug(f"[_validate_date] Input date_str is empty/None. Returning ''")
            return "" # Return empty string for None or empty input
        
        date_str = date_str.strip()
        if not date_str: # After stripping, if it becomes empty
            logger.debug(f"[_validate_date] Input date_str became empty after stripping. Returning ''")
            return ""

        # Try multiple common date and datetime formats
        # Added formats to handle time and AM/PM
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d', 
                    '%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', # 24-hour time
                    '%m/%d/%Y %I:%M:%S %p', '%Y-%m-%d %I:%M:%S %p'): # 12-hour time with AM/PM
            try:
                dt = datetime.strptime(date_str, fmt)
                formatted_date = dt.strftime('%Y-%m-%d') # Always store as APAC-MM-DD
                logger.debug(f"[_validate_date] Successfully parsed '{date_str}' with '{fmt}'. Returning '{formatted_date}'")
                return formatted_date
            except ValueError:
                logger.debug(f"[_validate_date] Failed to parse '{date_str}' with format '{fmt}'")
                continue # Try next format
        
        # If execution reaches here, it means date_str was not empty but could not be parsed
        logger.error(f"[_validate_date] Failed to parse date string '{date_str}' into any known format. Raising DataValidationError.")
        raise DataValidationError(f"Invalid date format: '{date_str}'. Expected APAC-MM-DD or common date/datetime format (e.g., MM/DD/YYYY, DD-MM-YYYY, or with time/AM/PM).")

    @staticmethod
    def _validate_string(value: Optional[str], field_name: str, max_len: int = 255, allow_empty: bool = True) -> str:
        """
        Validates and sanitizes string fields.
        Converts None to "UNKNOWN" if not allowed to be empty.
        Truncates to max_len and removes problematic characters.
        """
        if value is None:
            return "UNKNOWN" if not allow_empty else ""
        
        value = str(value).strip()
        
        if not value:
            return "UNKNOWN" if not allow_empty else ""
            
        # Basic sanitization: remove delimiters and newlines that could break CSV/JSON
        value = value.replace(';', ',').replace('\n', ' ').replace('\r', '')
        
        return value[:max_len] # Truncate to max_len

    @staticmethod
    def _validate_yes_no(value: Optional[str]) -> str:
        """Validates input for 'Yes'/'No' fields."""
        if value is None:
            return "NO"
        
        value = str(value).strip().lower()
        return "YES" if value in ('yes', 'y', 'true', '1') else "NO"

    @staticmethod
    def _validate_positive_int(value: Optional[str], field_name: str, min_val: int = 0) -> int:
        """Validates and converts a value to a non-negative integer."""
        try:
            # Handle empty string or None by returning min_val
            if value is None or value == '':
                return min_val
            
            num = int(float(value)) # Convert via float to handle "5.0"
            if num < min_val:
                logger.warning(f"Integer value for {field_name} ({num}) is less than minimum {min_val}. Setting to {min_val}.")
                return min_val
            return num
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val

    @staticmethod
    def _validate_positive_float(value: Optional[str], field_name: str, min_val: float = 0.0) -> float:
        """Validates and converts a value to a non-negative float."""
        try:
            # Handle empty string or None by returning min_val
            if value is None or value == '':
                return min_val
            
            num = float(value)
            if num < min_val:
                logger.warning(f"Float value for {field_name} ({num}) is less than minimum {min_val}. Setting to {min_val}.")
                return min_val
            return round(num, 2) # Round to 2 decimal places for consistency
        except (ValueError, TypeError):
            logger.warning(f"Invalid float value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val

    @staticmethod
    def _validate_range(value: Optional[str], field_name: str, min_val: int, max_val: int) -> int:
        """Validates a numeric field to be within a specific integer range."""
        try:
            # Handle empty string or None by returning min_val
            if value is None or value == '':
                return min_val
            
            num = int(float(value)) # Convert via float to handle "12.0"
            if not (min_val <= num <= max_val):
                logger.warning(f"Value for {field_name} ({num}) is out of range [{min_val}-{max_val}]. Setting to {min_val}.")
                return min_val # Default to min_val if out of range
            return num
        except (ValueError, TypeError):
            logger.warning(f"Invalid numeric value '{value}' for {field_name}. Setting to {min_val}.")
            return min_val
            
    def to_bytes(self) -> bytes:
        """
        Serializes the DataObject into bytes using JSON format.
        Uses sorted keys for consistent byte representation.
        """
        try:
            data_dict = {attr: getattr(self, attr) for attr in FIELDS}
            # Ensure JSON is compact and consistent for hashing
            return json.dumps(data_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
        except TypeError as e:
            logger.error(f"Serialization TypeError in DataObject: {e}. Data dict: {data_dict}")
            raise DatabaseError(f"Failed to serialize record due to invalid data type: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected serialization error in DataObject: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to serialize record: {str(e)}")

    @classmethod
    def from_bytes(cls, byte_data: bytes) -> 'DataObject':
        """
        Deserializes byte data back into a DataObject instance.
        Handles various deserialization errors.
        """
        if not byte_data:
            raise DataValidationError("Attempted to deserialize empty byte data.")
        
        try:
            data_dict = json.loads(byte_data.decode('utf-8'))
            obj = cls(existing_data_dict=data_dict) # Initialize using the dictionary constructor
            # Validation is already done in the DataObject constructor
            return obj
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"JSON/Unicode decode error during deserialization: {e} | Data: {byte_data[:100]}...")
            raise DatabaseError("Invalid data format during deserialization.")
        except DataValidationError as e:
            logger.error(f"Data validation error after deserialization: {e}")
            raise DatabaseError(f"Corrupt data after deserialization: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected deserialization error: {traceback.format_exc()}")
            raise DatabaseError(f"Failed to deserialize record: {str(e)}")

    def validate(self) -> bool:
        """
        Performs comprehensive semantic validation on the DataObject's fields.
        Ensures consistency and correctness of data.
        """
        try:
            # 1. Required fields check
            if not self.crash_date: 
                raise DataValidationError("Crash date is required.")
            if not self.crash_type or self.crash_type == "UNKNOWN":
                raise DataValidationError("Crash type is required.")
            if not isinstance(self.num_units, int) or self.num_units < 0:
                raise DataValidationError("Number of units must be a non-negative integer.")
            if not isinstance(self.injuries_total, (int, float)) or self.injuries_total < 0:
                raise DataValidationError("Total injuries must be a non-negative number.")
            
            # 2. Date format validation (already done by _validate_date but double-check)
            if self.crash_date: # Only check if not empty
                try:
                    datetime.strptime(self.crash_date, '%Y-%m-%d')
                except ValueError:
                    raise DataValidationError("Invalid crash date format (expected APAC-MM-DD).")
            
            # 3. Consistency checks for injuries
            total_reported_injuries = (
                self.injuries_fatal + self.injuries_incapacitating +
                self.injuries_non_incapacitating + self.injuries_reported_not_evident +
                self.injuries_no_indication
            )
            # Allow for slight floating point inaccuracies or where total includes unclassified injuries
            if self.injuries_total < total_reported_injuries - 0.01: # Small tolerance for float comparison
                logger.warning(f"Total injuries ({self.injuries_total}) less than sum of specific injuries ({total_reported_injuries}).")
                # For now, this is a warning, not an error that fails validation.
                # Could be changed to an error if strict consistency is required.
            
            # 4. Range validation (already done by _validate_range, but for robustness)
            if not (0 <= self.crash_hour <= 23):
                raise DataValidationError("Crash hour out of valid range (0-23).")
            if not (1 <= self.crash_day_of_week <= 7):
                raise DataValidationError("Crash day of week out of valid range (1-7).")
            if not (1 <= self.crash_month <= 12):
                raise DataValidationError("Crash month out of valid range (1-12).")

            return True
        except DataValidationError as e:
            logger.warning(f"DataObject validation failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during DataObject validation: {traceback.format_exc()}")
            return False
     