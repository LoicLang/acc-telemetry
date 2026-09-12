"""Time reports must not paint pedal measurements across unreviewed gaps."""
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
import plotly.graph_objects as go

from acc_telemetry.visualization.interactive import InteractiveTelemetryVisualizer


class TestTimeReportGaps(unittest.TestCase):
    def test_pedal_gaps_have_neither_measurement_lines_nor_bridging_fill(self):
        # A known input, two missing frames, then a released and reapplied pedal.
        df = pd.DataFrame({
            'time': [0., 1., 2., 3., 4.],
            'throttle': [100., None, None, 0., 100.],
            'brake': [0., None, None, 100., 0.],
            'steering': [None] * 5,
            'speed': [100., None, None, 80., 90.],
            'gear': [3.] * 5,
            'tc_active': [None] * 5,
            'abs_active': [None] * 5,
        })
        with tempfile.TemporaryDirectory() as directory:
            visualizer = InteractiveTelemetryVisualizer(directory)
            for subplots in (False, True):
                with self.subTest(subplots=subplots):
                    figures = []
                    with patch.object(go.Figure, 'write_html',
                                      lambda figure, *args, **kwargs: figures.append(figure)):
                        visualizer.plot_telemetry(df, use_subplots=subplots)
                    for trace in figures[0].data:
                        if trace.name not in ('Throttle', 'Brake'):
                            continue
                        self.assertIn(trace.fill, (None, 'none'),
                                      'tozeroy bridges missing intervals with false pedal area')
                        self.assertFalse(trace.connectgaps)
                        self.assertTrue(pd.isna(trace.y[1]))
                        self.assertTrue(pd.isna(trace.y[2]))
                        self.assertEqual(list(trace.y)[3:], list(df[trace.name.lower()])[3:])
