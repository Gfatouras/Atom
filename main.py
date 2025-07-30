#!/usr/bin/env python3
"""
Nuclear data processing script
Reads nuclear wallet cards data and creates a labeled pandas DataFrame with full decay mode names
"""

import pandas as pd
import numpy as np
import re


def get_decay_mode_mapping():
    """
    Returns a dictionary mapping decay mode abbreviations to full names
    """
    return {
        'B-': 'Beta minus decay',
        'B+': 'Beta plus decay',
        'EC': 'Electron capture',
        'IT': 'Isomeric transition',
        'A': 'Alpha decay',
        'P': 'Proton emission',
        'N': 'Neutron emission',
        '2N': 'Two neutron emission',
        '3N': 'Three neutron emission',
        '4N': 'Four neutron emission',
        '2P': 'Two proton emission',
        '3P': 'Three proton emission',
        'SF': 'Spontaneous fission',
        'BN': 'Beta minus + neutron emission',
        'B2N': 'Beta minus + two neutron emission',
        'BNA': 'Beta minus + neutron + alpha',
        'BA': 'Beta minus + alpha',
        'BP': 'Beta plus + proton',
        'B2P': 'Beta plus + two proton',
        'ECP': 'Electron capture + proton',
        'EP': 'Electron capture + proton',
        'EC2P': 'Electron capture + two proton',
        'ECA': 'Electron capture + alpha',
        'EA': 'Electron capture + alpha',
        'ECBP': 'Electron capture + beta plus',
        'PA': 'Proton + alpha emission',
        '2A': 'Two alpha decay',
        '3A': 'Three alpha decay',
        '14C': 'Carbon-14 cluster decay',
        '20O': 'Oxygen-20 cluster decay',
        'O': 'Oxygen cluster decay',
        '22NE': 'Neon-22 cluster decay',
        'Ne': 'Neon cluster decay',
        '24NE': 'Neon-24 cluster decay',
        '25NE': 'Neon-25 cluster decay',
        '28MG': 'Magnesium-28 cluster decay',
        'Mg': 'Magnesium cluster decay',
        '34SI': 'Silicon-34 cluster decay',
        'Si': 'Silicon cluster decay',
        'BF': 'Beta delayed fission',
        'EF': 'Electron capture delayed fission',
        '2C': 'Two carbon cluster decay',
        '4C': 'Four carbon cluster decay'
    }


def parse_nuclear_wallet_cards(filename):
    """
    Parse the nuclear wallet cards file and return a pandas DataFrame
    """
    
    # Define column specifications based on the fixed-width format
    # Carefully measured from the actual data format
    colspecs = [
        (0, 4),      # Mass number (A)
        (4, 9),      # Atomic number (Z)
        (9, 13),     # Element symbol
        (13, 15),    # Quality flag (Q/W)
        (15, 32),    # Spin and parity (J^π)
        (32, 35),    # Primary decay mode
        (35, 42),    # Branching ratio (%)
        (42, 50),    # Q-value uncertainty
        (50, 57),    # Q-value (MeV)
        (57, 75),    # Half-life
        (75, 99),    # Abundance or additional info
        (99, 107),   # Mass excess (keV)
        (107, 115),  # Mass excess uncertainty
        (115, 123),  # Reference
        (123, None)  # Half-life in seconds (to end of line)
    ]
    
    # Column names
    column_names = [
        'mass_number',
        'atomic_number', 
        'element_symbol',
        'quality_flag',
        'spin_parity',
        'decay_mode',
        'branching_ratio_percent',
        'q_value_uncertainty', 
        'q_value_mev',
        'half_life',
        'abundance_info',
        'mass_excess_kev',
        'mass_excess_uncertainty',
        'reference',
        'half_life_seconds'
    ]
    
    # Read the fixed-width file
    df = pd.read_fwf(filename, colspecs=colspecs, names=column_names, 
                     dtype=str, comment='!', skip_blank_lines=True)
    
    # Clean up the DataFrame
    df = df.dropna(how='all')  # Remove completely empty rows
    
    # Strip whitespace from string columns
    string_cols = ['element_symbol', 'quality_flag', 'spin_parity', 'decay_mode', 
                   'half_life', 'abundance_info', 'reference']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    # Convert numeric columns where appropriate
    numeric_columns = ['mass_number', 'atomic_number', 'branching_ratio_percent',
                      'q_value_uncertainty', 'q_value_mev', 'mass_excess_kev', 
                      'mass_excess_uncertainty', 'half_life_seconds']
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Expand decay mode abbreviations
    decay_mapping = get_decay_mode_mapping()
    
    def expand_decay_mode(mode_str):
        if pd.isna(mode_str) or mode_str.strip() == '' or mode_str == 'nan':
            return 'Stable'
        
        mode_str = str(mode_str).strip()
        
        # Remove special characters that indicate experimental conditions
        # but preserve them for notation
        original_mode = mode_str
        uncertainty_flags = []
        
        if '?' in mode_str:
            uncertainty_flags.append('uncertain')
            mode_str = mode_str.replace('?', '')
        if '#' in mode_str:
            uncertainty_flags.append('extrapolated')
            mode_str = mode_str.replace('#', '')
        if '&' in mode_str:
            uncertainty_flags.append('from systematics')
            mode_str = mode_str.replace('&', '')
        if '<' in mode_str:
            uncertainty_flags.append('less than')
            mode_str = mode_str.replace('<', '')
        if '>' in mode_str:
            uncertainty_flags.append('greater than')
            mode_str = mode_str.replace('>', '')
        if '@' in mode_str:
            uncertainty_flags.append('estimated')
            mode_str = mode_str.replace('@', '')
        
        mode_str = mode_str.strip()
        
        # Handle multiple decay modes separated by various delimiters
        modes = re.split(r'[,\s]+', mode_str)
        expanded_modes = []
        
        for mode in modes:
            mode = mode.strip()
            if mode == '':
                continue
            if mode in decay_mapping:
                expanded_modes.append(decay_mapping[mode])
            elif mode != '':
                expanded_modes.append(mode)
        
        result = ', '.join(expanded_modes) if expanded_modes else 'Stable'
        
        # Add uncertainty information
        if uncertainty_flags:
            result += f" ({', '.join(uncertainty_flags)})"
        
        return result
    
    # Apply decay mode expansion
    df['decay_mode_full'] = df['decay_mode'].apply(expand_decay_mode)
    
    return df


def main():
    """
    Main function to process nuclear data and display results
    """
    
    # File path
    nuclear_data_file = 'nuclear-wallet-cards.txt/nuclear-wallet-cards.txt'
    
    try:
        # Parse the nuclear wallet cards data
        df = parse_nuclear_wallet_cards(nuclear_data_file)
        
        print("Nuclear Wallet Cards Data Loaded Successfully!")
        print(f"Dataset shape: {df.shape}")
        print("\nColumn names:")
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2d}. {col}")
        
        print("\nColumn descriptions:")
        print("1. mass_number: Mass number (A) of the nuclide")
        print("2. atomic_number: Atomic number (Z) of the nuclide") 
        print("3. element_symbol: Chemical symbol of the element")
        print("4. quality_flag: Data quality indicator (Q=adopted, W=from NUBASE)")
        print("5. spin_parity: Nuclear spin and parity (J^π)")
        print("6. decay_mode: Primary decay mode abbreviation")
        print("7. branching_ratio_percent: Branching ratio percentage")
        print("8. q_value_uncertainty: Q-value uncertainty")
        print("9. q_value_mev: Q-value in MeV")
        print("10. half_life: Half-life with units")
        print("11. abundance_info: Natural abundance or additional notes")
        print("12. mass_excess_kev: Mass excess in keV")
        print("13. mass_excess_uncertainty: Mass excess uncertainty")
        print("14. reference: Literature reference")
        print("15. half_life_seconds: Half-life converted to seconds")
        print("16. decay_mode_full: Full decay mode name with uncertainty flags")
        
        print("\nFirst few rows:")
        print(df.head())
        
        print("\nSample of decay modes (original vs expanded):")
        decay_sample = df[['element_symbol', 'mass_number', 'decay_mode', 'decay_mode_full']].head(15)
        for _, row in decay_sample.iterrows():
            if pd.notna(row['mass_number']) and pd.notna(row['element_symbol']):
                print(f"{row['element_symbol']}-{int(row['mass_number'])}: '{row['decay_mode']}' -> '{row['decay_mode_full']}'")
        
        print("\nUnique decay modes found:")
        unique_decay_modes = df['decay_mode'].dropna().unique()
        for mode in sorted(unique_decay_modes):
            if mode.strip() != '':
                print(f"  '{mode}'")
        
        # Save to CSV for further analysis
        output_file = 'nuclear_data_processed.csv'
        df.to_csv(output_file, index=False)
        print(f"\nData saved to: {output_file}")
        
        return df
        
    except FileNotFoundError:
        print(f"Error: Could not find file '{nuclear_data_file}'")
        print("Please ensure the nuclear wallet cards file is in the correct location.")
        return None
    except Exception as e:
        print(f"Error processing file: {e}")
        return None


if __name__ == "__main__":
    df = main()