/**
 * Instancia de ECharts TREE-SHAKEN: se importa de `echarts/core` y se registran SOLO los charts,
 * componentes y el renderer que usa la Fase 1 (no el bundle completo). Cualquier gráfica nueva debe
 * añadir aquí lo que necesite (p.ej. un chart type adicional).
 */
import * as echarts from "echarts/core";
import {
  LineChart,
  BarChart,
  ScatterChart,
  HeatmapChart,
  CustomChart,
  FunnelChart,
} from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  MarkPointComponent,
  MarkLineComponent,
  VisualMapComponent,
  LegendComponent,
  DataZoomComponent,
  GraphicComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
  LineChart,
  BarChart,
  ScatterChart,
  HeatmapChart,
  CustomChart,
  FunnelChart,
  GridComponent,
  TooltipComponent,
  MarkPointComponent,
  MarkLineComponent,
  VisualMapComponent,
  LegendComponent,
  DataZoomComponent,
  GraphicComponent,
  CanvasRenderer,
]);

export { echarts };
