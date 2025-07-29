import pandas as pd

# Tạo DataFrame mẫu
data = {
    'factor': [10, 20, 20, 30, 10]
}
df = pd.DataFrame(data)

# Xếp hạng tăng dần (ascending=True) với method='first'
df['rank_ascending'] = df['factor'].rank(ascending=True, method='first')

# Xếp hạng giảm dần (ascending=False) với method='first'
df['rank_descending'] = df['factor'].rank(ascending=False, method='first')

# Xếp hạng tăng dần với method='average'
df['rank_average'] = df['factor'].rank(ascending=True, method='average')

print(df)