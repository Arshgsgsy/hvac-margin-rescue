import pandas as pd

ROLE_MAP = {
    'JM Pipefitter': 'Journeyman Pipefitter',
    'J. Pipefitter': 'Journeyman Pipefitter',
    'Pipefitter JM': 'Journeyman Pipefitter',
    'Journeyman P.F.': 'Journeyman Pipefitter',
    'Sheet Metal JM': 'Journeyman Sheet Metal',
    'J. Sheet Metal': 'Journeyman Sheet Metal',
    'JM Sheet Metal': 'Journeyman Sheet Metal',
    'Journeyman S.M.': 'Journeyman Sheet Metal',
    'Apprentice 2nd Yr': 'Apprentice 2nd Year',
    'App 2nd Year': 'Apprentice 2nd Year',
    'Apprentice - 2nd': 'Apprentice 2nd Year',
    'Apprentice 4th Yr': 'Apprentice 4th Year',
    'App 4th Year': 'Apprentice 4th Year',
    'Apprentice - 4th': 'Apprentice 4th Year',
    '4th Yr Apprentice': 'Apprentice 4th Year',
    'Helper': 'Helper/Laborer',
    'Fmn': 'Foreman',
    'Lead Foreman': 'Foreman',
    'General Foreman': 'Foreman',
    'Controls Tech': 'Controls Technician',
    'DDC Tech': 'Controls Technician',
    'Ctrl Technician': 'Controls Technician',
    'Controls Specialist': 'Controls Technician',
}

df = pd.read_csv('data/labor_logs_all.csv')

df['clean_role'] = df['role'].map(ROLE_MAP).fillna(df['role'])

print(df['clean_role'].value_counts())