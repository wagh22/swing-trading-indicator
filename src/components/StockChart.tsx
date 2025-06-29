import React, { useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  TimeScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
} from 'chart.js';
import { Chart } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';
import { ChartData } from '../types/stock';
import { X } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  TimeScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

interface StockChartProps {
  chartData: ChartData;
  onClose: () => void;
}

export const StockChart: React.FC<StockChartProps> = ({ chartData, onClose }) => {
  const chartRef = useRef<ChartJS>(null);

  const data = {
    labels: chartData.data.map(d => d.time),
    datasets: [
      {
        label: 'Price',
        data: chartData.data.map(d => ({
          x: d.time,
          y: d.close,
        })),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.1,
      },
      {
        label: 'Support Level',
        data: chartData.data.map(d => ({
          x: d.time,
          y: chartData.supportLevels[0],
        })),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
      },
      {
        label: 'Resistance Level',
        data: chartData.data.map(d => ({
          x: d.time,
          y: chartData.resistanceLevels[0],
        })),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: 'rgb(156, 163, 175)',
        },
      },
      title: {
        display: true,
        text: `${chartData.symbol} - Technical Analysis`,
        color: 'rgb(255, 255, 255)',
        font: {
          size: 16,
        },
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: 'day' as const,
        },
        grid: {
          color: 'rgb(75, 85, 99)',
        },
        ticks: {
          color: 'rgb(156, 163, 175)',
        },
      },
      y: {
        grid: {
          color: 'rgb(75, 85, 99)',
        },
        ticks: {
          color: 'rgb(156, 163, 175)',
          callback: function(value: any) {
            return '₹' + value.toFixed(2);
          },
        },
      },
    },
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-lg w-full max-w-4xl h-96 p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-white">Chart Analysis</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        
        <div className="h-80">
          <Chart ref={chartRef} type="line" data={data} options={options} />
        </div>
      </div>
    </div>
  );
};