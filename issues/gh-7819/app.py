import streamlit as st

st.markdown(
    """
这是一个Python函数，它接受一个pandas的DataFrame，并计算除\'Tag\'列外所有列的数据统计。如果结果是字典或pandas的Series，它会将其转换为DataFrame。如果无法计算，它会返回一个字符串，说明原因。\n\n```python\nimport pandas as pd\n\ndef func(df):\n    try:\n        # 检查\'Tag\'列是否存在\n        if \'Tag\' not in df.columns:\n            return "DataFrame中不存在\'Tag\'列。"\n        \n        # 计算除\'Tag\'列外所有列的数据统计\n        result = df.drop(\'Tag\', axis=1).describe()\n        \n        # 如果结果是字典或Series，将其转换为DataFrame\n        if isinstance(result, pd.Series):\n            result = result.to_frame()\n        \n        return result\n    except Exception as e:\n        return f"无法计算数据统计。原因：{str(e)}"\n```\n\n这个函数首先检查\'Tag\'列是否存在。如果不存在，它会返回一个字符串，说明原因。然后，它计算除\'Tag\'列外所有列的数据统计。如果结果是字典或Series，它会将其转换为DataFrame。如果在计算过程中出现任何错误，它会捕获异常并返回一个字符串，说明原因。\n\n注意：这个函数假设你已经导入了pandas库。如果没有导入，你需要在函数开头添加`import pandas as pd`。\n<|EOT|>
"""
)
