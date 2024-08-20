import streamlit as st


TABLE_CORRECT = """
TEXT

<table class="- topic/table table frame-all" style="width:100%;">
<colgroup>
<col style="width: 50%">
<col style="width: 50%">
</colgroup>

  <thead class="- topic/thead thead">
    <tr class="- topic/row">
      <th id="header1" class="- topic/entry entry colsep-1 rowsep-1">
        Property
      </th>
      <th id="header2" class="- topic/entry entry colsep-1 rowsep-1">
        Description
      </th>
    </tr>
  </thead>
  <tbody class="- topic/tbody tbody">
    <tr class="- topic/row">
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header1">
        ExampleProperty1
      </td>
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header2">
        Description of ExampleProperty1
      </td>
    </tr>
    <tr class="- topic/row">
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header1">
        ExampleProperty2
      </td>
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header2">
        Description of ExampleProperty2
      </td>
    </tr>
    <tr class="- topic/row">
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header1">
        ExampleProperty3
      </td>
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header2">
        Description of ExampleProperty3
      </td>
    </tr>
    <tr class="- topic/row">
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header1">
        ExampleProperty4
      </td>
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header2">
        Description of ExampleProperty4
      </td>
    </tr>
  </tbody>
</table>
"""

TABLE_FAULTY_1 = """
TEXT

<table class="- topic/table table frame-all" style="width:100%;">
<colgroup>

<col style="width: 50%">
<col style="width: 50%">
</colgroup>

  <thead class="- topic/thead thead">
    <tr class="- topic/row">
      <th id="header1" class="- topic/entry entry colsep-1 rowsep-1">
        Property
      </th>
      <th id="header2" class="- topic/entry entry colsep-1 rowsep-1">
        Description
      </th>
    </tr>
  </thead>
  <tbody class="- topic/tbody tbody">
    <tr class="- topic/row">
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header1">
        ExampleProperty1
      </td>
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header2">
        Description of ExampleProperty1
      </td>
    </tr>
    <tr class="- topic/row">
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header1">
        ExampleProperty2
      </td>
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header2">
        Description of ExampleProperty2
      </td>
    </tr>
    <tr class="- topic/row">
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header1">
        ExampleProperty3
      </td>
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header2">
        Description of ExampleProperty3
      </td>
    </tr>
    <tr class="- topic/row">
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header1">
        ExampleProperty4
      </td>
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header2">
        Description of ExampleProperty4
      </td>
    </tr>
  </tbody>
</table>
"""

TABLE_FAULTY_2 = """
TEXT

<table class="- topic/table table frame-all" style="width:100%;">
<colgroup>

    <col style="width: 50%">
    <col style="width: 50%">
</colgroup>

  <thead class="- topic/thead thead">
    <tr class="- topic/row">
      <th id="header1" class="- topic/entry entry colsep-1 rowsep-1">
        Property
      </th>
      <th id="header2" class="- topic/entry entry colsep-1 rowsep-1">
        Description
      </th>
    </tr>
  </thead>
  <tbody class="- topic/tbody tbody">
    <tr class="- topic/row">
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header1">
        ExampleProperty1
      </td>
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header2">
        Description of ExampleProperty1
      </td>
    </tr>
    <tr class="- topic/row">
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header1">
        ExampleProperty2
      </td>
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header2">
        Description of ExampleProperty2
      </td>
    </tr>
    <tr class="- topic/row">
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header1">
        ExampleProperty3
      </td>
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header2">
        Description of ExampleProperty3
      </td>
    </tr>
    <tr class="- topic/row">
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header1">
        ExampleProperty4
      </td>
      <td class="- topic/entry entry colsep-1 rowsep-1" headers="header2">
        Description of ExampleProperty4
      </td>
    </tr>
  </tbody>
</table>
"""

st.markdown(TABLE_CORRECT, unsafe_allow_html=True)
st.markdown(TABLE_FAULTY_1, unsafe_allow_html=True)
st.markdown(TABLE_FAULTY_2, unsafe_allow_html=True)
