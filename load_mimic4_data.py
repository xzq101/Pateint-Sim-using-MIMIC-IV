"""
MIMIC-IV Hospital Data Loader
This script loads MIMIC-IV hospital data from CSV files.
"""

import pandas as pd
import os
from pathlib import Path

class MIMIC4DataLoader:
    def __init__(self, data_dir='../../mimic_4/hosp', ed_dir='../../mimic_4/ed'):
        """
        Initialize the MIMIC-IV data loader.
        
        Args:
            data_dir: Path to the MIMIC-IV hospital data directory
            ed_dir: Path to the MIMIC-IV-ED data directory
        """
        self.data_dir = Path(data_dir).resolve()
        self.ed_dir = Path(ed_dir).resolve()
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        if not self.ed_dir.exists():
            print(f"Warning: ED directory not found: {self.ed_dir}")
    
    def _get_file_path(self, filename, directory=None):
        """Find file with .csv or .csv.gz extension"""
        if directory is None:
            directory = self.data_dir
        base_name = filename.replace('.csv', '')
        # Try .csv.gz first, then .csv
        for ext in ['.csv.gz', '.csv']:
            file_path = directory / f"{base_name}{ext}"
            if file_path.exists():
                return file_path
        raise FileNotFoundError(f"File not found: {base_name}.csv or {base_name}.csv.gz")
    
    def load_admissions(self):
        """Load admissions.csv or admissions.csv.gz"""
        file_path = self._get_file_path('admissions.csv')
        print(f"Loading {file_path.name}...")
        return pd.read_csv(file_path)
    
    def load_patients(self):
        """Load patients.csv or patients.csv.gz"""
        file_path = self._get_file_path('patients.csv')
        print(f"Loading {file_path.name}...")
        return pd.read_csv(file_path)
    
    def load_diagnoses_icd(self):
        """Load diagnoses_icd.csv or diagnoses_icd.csv.gz"""
        file_path = self._get_file_path('diagnoses_icd.csv')
        print(f"Loading {file_path.name}...")
        return pd.read_csv(file_path)
    
    def load_procedures_icd(self):
        """Load procedures_icd.csv or procedures_icd.csv.gz"""
        file_path = self._get_file_path('procedures_icd.csv')
        print(f"Loading {file_path.name}...")
        return pd.read_csv(file_path)
    
    def load_labevents(self, nrows=None):
        """
        Load labevents.csv or labevents.csv.gz (can be very large)
        
        Args:
            nrows: Number of rows to load (None for all)
        """
        file_path = self._get_file_path('labevents.csv')
        print(f"Loading {file_path.name}...")
        if nrows:
            print(f"  Loading first {nrows} rows...")
        return pd.read_csv(file_path, nrows=nrows)
    
    def load_prescriptions(self):
        """Load prescriptions.csv or prescriptions.csv.gz"""
        file_path = self._get_file_path('prescriptions.csv')
        print(f"Loading {file_path.name}...")
        return pd.read_csv(file_path)
    
    # MIMIC-IV-ED specific tables
    def load_ed_stays(self):
        """Load ED stays (edstays.csv)"""
        file_path = self._get_file_path('edstays.csv', directory=self.ed_dir)
        print(f"Loading {file_path.name}...")
        return pd.read_csv(file_path)
    
    def load_ed_triage(self):
        """Load ED triage (triage.csv) - includes chiefcomplaint and pain"""
        file_path = self._get_file_path('triage.csv', directory=self.ed_dir)
        print(f"Loading {file_path.name}...")
        return pd.read_csv(file_path)
    
    def load_ed_medrecon(self):
        """Load ED medication reconciliation (medrecon.csv)"""
        file_path = self._get_file_path('medrecon.csv', directory=self.ed_dir)
        print(f"Loading {file_path.name}...")
        return pd.read_csv(file_path)
    
    def load_ed_diagnosis(self):
        """Load ED diagnosis (diagnosis.csv)"""
        file_path = self._get_file_path('diagnosis.csv', directory=self.ed_dir)
        print(f"Loading {file_path.name}...")
        return pd.read_csv(file_path)
    
    def load_d_icd_diagnoses(self):
        """Load d_icd_diagnoses.csv or d_icd_diagnoses.csv.gz (dictionary)"""
        file_path = self._get_file_path('d_icd_diagnoses.csv')
        print(f"Loading {file_path.name}...")
        return pd.read_csv(file_path)
    
    def load_d_icd_procedures(self):
        """Load d_icd_procedures.csv or d_icd_procedures.csv.gz (dictionary)"""
        file_path = self._get_file_path('d_icd_procedures.csv')
        print(f"Loading {file_path.name}...")
        return pd.read_csv(file_path)
    
    def load_d_labitems(self):
        """Load d_labitems.csv or d_labitems.csv.gz (dictionary)"""
        file_path = self._get_file_path('d_labitems.csv')
        print(f"Loading {file_path.name}...")
        return pd.read_csv(file_path)
    
    def load_all_core_tables(self):
        """
        Load all core MIMIC-IV hospital tables.
        
        Returns:
            dict: Dictionary containing all loaded dataframes
        """
        data = {}
        
        try:
            data['admissions'] = self.load_admissions()
            data['patients'] = self.load_patients()
            data['diagnoses_icd'] = self.load_diagnoses_icd()
            data['procedures_icd'] = self.load_procedures_icd()
            data['prescriptions'] = self.load_prescriptions()
            
            # Load dictionaries
            data['d_icd_diagnoses'] = self.load_d_icd_diagnoses()
            data['d_icd_procedures'] = self.load_d_icd_procedures()
            data['d_labitems'] = self.load_d_labitems()
            
            print("\nAll core tables loaded successfully!")
            return data
        
        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("Available files in directory:")
            for file in self.data_dir.glob('*.csv'):
                print(f"  - {file.name}")
            return data
    
    def list_available_files(self):
        """List all CSV and CSV.GZ files in the data directory"""
        csv_files = list(self.data_dir.glob('*.csv')) + list(self.data_dir.glob('*.csv.gz'))
        print(f"Found {len(csv_files)} CSV/CSV.GZ files in {self.data_dir}:")
        for file in sorted(csv_files):
            file_size = file.stat().st_size / (1024**2)  # Size in MB
            print(f"  - {file.name} ({file_size:.2f} MB)")
        return csv_files


def main():
    """Example usage"""
    # Initialize the data loader
    loader = MIMIC4DataLoader(data_dir='../../mimic_4/hosp')
    
    # Load admissions table
    print("=" * 60)
    print("Loading Admissions Table")
    print("=" * 60)
    
    admissions = loader.load_admissions()
    
    print(f"\nShape: {admissions.shape}")
    print(f"\nColumns: {admissions.columns.tolist()}")
    print(f"\nFirst few rows:")
    print(admissions.head())
    print(f"\nData types:")
    print(admissions.dtypes)
    print(f"\nBasic statistics:")
    print(admissions.describe())
    
    return admissions


if __name__ == "__main__":
    admissions = main()
