/**
 * Smart Watchlist — Lightweight Financial Canvas Chart
 */

class FinancialChart {
  constructor(canvasElement) {
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext('2d');
    this.data = [];
    this.hoverIndex = -1;
    this.isPositive = true;

    this.initEvents();
  }

  initEvents() {
    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      if (this.data.length > 1) {
        const paddingLeft = 10;
        const paddingRight = 60;
        const width = this.canvas.width / (window.devicePixelRatio || 1) - paddingLeft - paddingRight;
        const ratio = Math.max(0, Math.min(1, (x - paddingLeft) / width));
        this.hoverIndex = Math.round(ratio * (this.data.length - 1));
        this.render();
      }
    });

    this.canvas.addEventListener('mouseleave', () => {
      this.hoverIndex = -1;
      this.render();
    });
  }

  setData(candles) {
    this.data = candles || [];
    if (this.data.length >= 2) {
      const first = this.data[0].close;
      const last = this.data[this.data.length - 1].close;
      this.isPositive = last >= first;
    } else {
      this.isPositive = true;
    }
    this.render();
  }

  render() {
    if (!this.canvas) return;

    // Handle high DPI
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    if (this.canvas.width !== width * dpr || this.canvas.height !== height * dpr) {
      this.canvas.width = width * dpr;
      this.canvas.height = height * dpr;
    }

    const ctx = this.ctx;
    ctx.resetTransform();
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, width, height);

    if (!this.data || this.data.length < 2) {
      ctx.fillStyle = '#64748b';
      ctx.font = '14px Plus Jakarta Sans, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('No historical market data available for this range.', width / 2, height / 2);
      return;
    }

    const paddingTop = 20;
    const paddingBottom = 30;
    const paddingLeft = 15;
    const paddingRight = 65;

    const chartWidth = width - paddingLeft - paddingRight;
    const chartHeight = height - paddingTop - paddingBottom;

    // Calculate Min & Max Close
    let minPrice = Infinity;
    let maxPrice = -Infinity;
    for (const d of this.data) {
      if (d.close < minPrice) minPrice = d.close;
      if (d.close > maxPrice) maxPrice = d.close;
    }

    const priceSpan = maxPrice - minPrice || 1;
    const yBuffer = priceSpan * 0.08;
    const chartMin = minPrice - yBuffer;
    const chartMax = maxPrice + yBuffer;
    const effectiveSpan = chartMax - chartMin;

    const getY = (price) => paddingTop + chartHeight - ((price - chartMin) / effectiveSpan) * chartHeight;
    const getX = (idx) => paddingLeft + (idx / (this.data.length - 1)) * chartWidth;

    // 1. Draw Grid Lines & Price Axis Labels
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#64748b';
    ctx.font = '11px JetBrains Mono, monospace';
    ctx.textAlign = 'left';

    const gridSteps = 4;
    for (let i = 0; i <= gridSteps; i++) {
      const p = chartMin + (effectiveSpan / gridSteps) * i;
      const y = getY(p);
      ctx.beginPath();
      ctx.moveTo(paddingLeft, y);
      ctx.lineTo(width - paddingRight, y);
      ctx.stroke();

      ctx.fillText(p.toFixed(1), width - paddingRight + 8, y + 4);
    }

    // 2. Draw Area Gradient
    const strokeColor = this.isPositive ? '#10b981' : '#ef4444';
    const gradColor = this.isPositive ? 'rgba(16, 185, 129, ' : 'rgba(239, 68, 68, ';

    const gradient = ctx.createLinearGradient(0, paddingTop, 0, paddingTop + chartHeight);
    gradient.addColorStop(0, `${gradColor}0.25)`);
    gradient.addColorStop(1, `${gradColor}0.0)`);

    ctx.beginPath();
    ctx.moveTo(getX(0), getY(this.data[0].close));
    for (let i = 1; i < this.data.length; i++) {
      ctx.lineTo(getX(i), getY(this.data[i].close));
    }
    ctx.lineTo(getX(this.data.length - 1), paddingTop + chartHeight);
    ctx.lineTo(getX(0), paddingTop + chartHeight);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // 3. Draw Main Price Line
    ctx.beginPath();
    ctx.moveTo(getX(0), getY(this.data[0].close));
    for (let i = 1; i < this.data.length; i++) {
      ctx.lineTo(getX(i), getY(this.data[i].close));
    }
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2.2;
    ctx.lineJoin = 'round';
    ctx.stroke();

    // 4. Draw Date Labels along bottom
    ctx.fillStyle = '#64748b';
    ctx.font = '11px Plus Jakarta Sans, sans-serif';
    ctx.textAlign = 'center';
    const dateInterval = Math.floor(this.data.length / 4);
    for (let i = 0; i < this.data.length; i += dateInterval) {
      const d = this.data[i];
      const x = getX(i);
      const dateLabel = (d.timestamp || '').split(' ')[0];
      ctx.fillText(dateLabel, x, height - 10);
    }

    // 5. Draw Hover Crosshair and Tooltip
    if (this.hoverIndex >= 0 && this.hoverIndex < this.data.length) {
      const activePoint = this.data[this.hoverIndex];
      const hx = getX(this.hoverIndex);
      const hy = getY(activePoint.close);

      // Vertical line
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(hx, paddingTop);
      ctx.lineTo(hx, paddingTop + chartHeight);
      ctx.stroke();

      // Horizontal line
      ctx.beginPath();
      ctx.moveTo(paddingLeft, hy);
      ctx.lineTo(width - paddingRight, hy);
      ctx.stroke();
      ctx.setLineDash([]);

      // Point circle
      ctx.beginPath();
      ctx.arc(hx, hy, 5, 0, Math.PI * 2);
      ctx.fillStyle = strokeColor;
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Tooltip Card
      const priceText = `${activePoint.close.toFixed(2)}`;
      const timeText = activePoint.timestamp || '';
      const tooltipText = `${priceText} | ${timeText}`;

      ctx.font = '12px JetBrains Mono, monospace';
      const textWidth = ctx.measureText(tooltipText).width;
      const boxWidth = textWidth + 18;
      const boxHeight = 26;
      let boxX = hx - boxWidth / 2;
      boxX = Math.max(paddingLeft, Math.min(boxX, width - paddingRight - boxWidth));
      const boxY = Math.max(5, hy - boxHeight - 10);

      ctx.fillStyle = '#0f1422';
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(boxX, boxY, boxWidth, boxHeight, 5);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#f8fafc';
      ctx.textAlign = 'left';
      ctx.fillText(tooltipText, boxX + 9, boxY + 17);
    }
  }
}

window.FinancialChart = FinancialChart;
