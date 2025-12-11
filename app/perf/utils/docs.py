METRIC_DEFINITIONS = """
#### Global Metrics

- **Long Animation Frame**: A long animation frame in Chrome DevTools refers to
a frame that takes longer than 16.67 milliseconds to render. This is significant
because, for smooth animations, the browser needs to render frames at 60 frames
per second (FPS). If a frame takes longer than 16.67 milliseconds, it can cause
jank or stutter in the animation, leading to a poor user experience. [MDN
Docs](https://developer.mozilla.org/en-US/docs/Web/API/Performance_API/Long_animation_frame_timing)

- **Script Run Cycle**: The start and end time of when a Streamlit script run
state goes from `running` to `not_running`. This is a custom [User
Timing](https://developer.mozilla.org/en-US/docs/Web/API/Performance_API/User_timing)
metric that is in the Streamlit codebase. It is useful to utilize as a way of
lining up the performance metrics with the Streamlit script run cycle.

#### React Metrics

- **Mount**: When a component is first added to the DOM. This is the first time
    the component is rendered.

- **Update**: An `update` in React Profiler refers to the process where a
component is re-rendered due to changes in state or props. This can happen for
various reasons such as user interactions, network responses, or any other
events that trigger a state change.

    Having too many updates in the following cases could point to performance
    issues:

    - Without user input
    - Too frequently for what the user is doing
    - Without any visible changes to the user
    - Without any changes to the data

    Fixing these issues could involve (but not limited to):

    - Using `React.memo` to prevent unnecessary re-renders - Using `useMemo` to
      memoize expensive calculations
    - Using `useCallback` to memoize event handlers
    - Stabilizing arrays and objects to prevent unnecessary re-renders

- **Nested Update**: "State updates that are scheduled in a layout effect
  (`useLayoutEffect` or `componentDidMount` / `componentDidUpdate`) get
  processed **synchronously** by React before it yields to the browser to paint.
  This is done so that components can adjust their layout (e.g. position and
  size a tooltip) without any visible shifting being seen by users. This type of
  update is often called a "nested update" or a "cascading update".

  Because they delay paint and block the main (JavaScript) thread, nested
  updates are considered expensive and should be avoided when possible. For
  example, effects that do not impact layout (e.g. adding event handlers,
  logging impressions) can be safely deferred to the passive effect phase by
  using `useEffect` instead."

  Source: [React PR #20163](https://github.com/facebook/react/pull/20163)

#### Location

- **Global**: Metrics that are not tied to a specific component or phase.
  Generally these come from the browser's performance API.

- **Main/Sidebar/Event/Bottom**: These are the name of the instances of [React
Profiler](https://react.dev/reference/react/Profiler) in the Streamlit codebase.
They are the React component boundaries that we created to help us understand
the performance of different parts of the Streamlit app. Search for `<Profiler`
in the Streamlit codebase to find them ([GitHub search
here](https://github.com/search?q=repo%3Astreamlit%2Fstreamlit%20%3CProfiler&type=code)).
"""
