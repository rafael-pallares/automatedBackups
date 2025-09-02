import enum

class DeviceCode(enum.Enum):
    SM = '91'
    SD = 'A9'
    X = '9C'
    Y = '9D'
    M = '90'
    L = '92'
    F = '93'
    V = '94'
    B = 'A0'
    D = 'A8'
    W = 'B4'
    TS = 'C1'
    TC = 'C0'
    TN = 'C2'
    LTS = '51'
    LTC = '50'
    LTN = '52'
    SS = 'C7'
    SC = 'C6'
    SN = 'C8'
    LSTS = '59'
    LSTC = '58'
    LSTN = '5A'
    CS = 'C4'
    CC = 'C3'
    CN = 'C5'
    SB = 'A1'
    SW = 'B5'
    DX = 'A2'
    DY = 'A3'
    Z = 'CC'
    LZ = '62'
    R = 'AF'
    ZR = 'B0'
    RD = '2C'
    LCS = '55'
    LCC = '54'
    LCN = '56'


class BackupMode(enum.Enum):
    default = 1
    default_c = 2
    full = 3