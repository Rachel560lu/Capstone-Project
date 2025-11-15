import React, { useState, useEffect, useRef } from 'react';
import './styles/App.css';
import MandalaBackground from './components/MandalaBackground';
import UploadSection from './components/UploadSection';
import FeaturesSection from './components/FeaturesSection';
import TutorialSection from './components/TutorialSection';
import LoadingOverlay from './components/LoadingOverlay';
import ErrorMessage from './components/ErrorMessage';
import Sidebar from './components/Sidebar';
// PDF libraries will be imported dynamically

const API_BASE_URL = 'http://localhost:5001';

function App() {
  const [selectedModule, setSelectedModule] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [originalUrl, setOriginalUrl] = useState('');
  const [processedUrl, setProcessedUrl] = useState('');
  const [showComparison, setShowComparison] = useState(false);
  const [taskId, setTaskId] = useState('');
  
  // Virtual staging parameters
  const [decorationStyle, setDecorationStyle] = useState('modern');
  const [maxPrice, setMaxPrice] = useState(50000);
  const [roomType, setRoomType] = useState('living room');
  
  // Virtual staging results
  const [furnitureList, setFurnitureList] = useState([]);
  const [furnitureImages, setFurnitureImages] = useState({});
  
  // Sliding comparison related
  const comparisonContainerRef = useRef(null);
  const sliderRef = useRef(null);
  const afterImageRef = useRef(null);
  const [isMoving, setIsMoving] = useState(false);

  const handleModuleSelect = (moduleId) => {
    setSelectedModule(moduleId);
    setError('');
    setShowComparison(false);
    setOriginalUrl('');
    setProcessedUrl('');
    setTaskId('');
    // Reset virtual staging parameters
    setDecorationStyle('modern');
    setMaxPrice(50000);
    setRoomType('living room');
    // Reset virtual staging results
    setFurnitureList([]);
    setFurnitureImages({});
  };

  const handleReupload = () => {
    setShowComparison(false);
    setOriginalUrl('');
    setProcessedUrl('');
    setTaskId('');
    setError('');
    setFurnitureList([]);
    setFurnitureImages({});
  };

  const handleDenoise = async () => {
    if (!originalUrl || !taskId) return;
    
    setIsLoading(true);
    setError('');
    setProcessedUrl(''); // Clear previous processing result
    
    try {
      // Call backend API to trigger Clutter Removal processing
      const response = await fetch(`${API_BASE_URL}/process-task`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: taskId,
          task_type: 'denoise'
        })
      });

      const result = await response.json();

      if (result.success) {
        // Start polling task status, wait for processing to complete
        await pollTaskResult(taskId);
      } else {
        setError(result.error || 'Processing failed, please try again');
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Processing error:', error);
      setError('Network error, please check if the backend service is running');
      setIsLoading(false);
    }
  };

  const pollTaskResult = async (taskId) => {
    const maxAttempts = 60; // Maximum 60 polling attempts
    const pollInterval = 2000; // Poll every 2 seconds
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/task/${taskId}/result`);
        const result = await response.json();

        if (result.success && result.processed_url) {
          // Processing complete, display result
          setProcessedUrl(`${API_BASE_URL}${result.processed_url}`);
          
          // Handle virtual staging results (furniture list and images)
          if (result.furniture_list) {
            setFurnitureList(result.furniture_list);
          }
          if (result.furniture_images) {
            const imagesMap = {};
            result.furniture_images.forEach(item => {
              imagesMap[item.model_id] = `${API_BASE_URL}${item.image_url}`;
            });
            setFurnitureImages(imagesMap);
          }
          
          setIsLoading(false);
          return;
        } else if (result.status === 'processing' || result.status === 'queued') {
          // Still processing, continue polling
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(poll, pollInterval);
          } else {
            setError('Processing timeout, please try again');
            setIsLoading(false);
          }
        } else if (result.status === 'failed') {
          setError(result.error || 'Processing failed, please try again');
          setIsLoading(false);
        } else {
          // Continue waiting
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(poll, pollInterval);
          } else {
            setError('Processing timeout, please try again');
            setIsLoading(false);
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, pollInterval);
        } else {
          setError('Failed to get processing result, please try again');
          setIsLoading(false);
        }
      }
    };

    // Start polling
    setTimeout(poll, pollInterval);
  };

  const handleVirtualDecorate = async () => {
    if (!originalUrl || !taskId) return;
    
    setIsLoading(true);
    setError('');
    setProcessedUrl(''); // Clear previous processing result
    setFurnitureList([]);
    setFurnitureImages({});
    
    try {
      // Call backend API to trigger virtual staging processing, pass decoration parameters
      const response = await fetch(`${API_BASE_URL}/process-task`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: taskId,
          task_type: 'virtual',
          decoration_style: decorationStyle,
          max_price: maxPrice,
          room_type: roomType
        })
      });

      const result = await response.json();

      if (result.success) {
        // Start polling task status, wait for processing to complete
        await pollTaskResult(taskId);
      } else {
        setError(result.error || 'Processing failed, please try again');
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Processing error:', error);
      setError('Network error, please check if the backend service is running');
      setIsLoading(false);
    }
  };

  const handleBackToHome = () => {
    setSelectedModule(null);
    setShowComparison(false);
    setOriginalUrl('');
    setProcessedUrl('');
    setTaskId('');
    setError('');
    setFurnitureList([]);
    setFurnitureImages({});
  };

  const handleGoStaging = async () => {
    // 切换到 virtual staging 模块，使用处理后的图片作为新的原始图片
    if (!processedUrl) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      // 将处理后的图片作为新的原始图片上传到 virtual staging
      const response = await fetch(processedUrl);
      const blob = await response.blob();
      const file = new File([blob], 'processed_image.png', { type: 'image/png' });
      
      // 创建 FormData 并上传
      const formData = new FormData();
      formData.append('image', file);
      formData.append('task_type', 'virtual');
      
      const uploadResponse = await fetch(`${API_BASE_URL}/upload-image`, {
        method: 'POST',
        body: formData
      });
      
      const result = await uploadResponse.json();
      
      if (result.success) {
        // 切换到 virtual staging 模块
        setSelectedModule('virtual');
        // 使用新上传的图片作为原始图片
        setOriginalUrl(`${API_BASE_URL}${result.original_url}`);
        setTaskId(result.task_id);
        // 清空处理结果，让用户可以重新选择参数
        setProcessedUrl('');
        setFurnitureList([]);
        setFurnitureImages({});
        // 显示图片和参数选择界面
        setShowComparison(true);
      } else {
        setError(result.error || 'Failed to upload image for virtual staging');
      }
    } catch (error) {
      console.error('Go staging error:', error);
      setError('Failed to switch to virtual staging');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadImage = async () => {
    if (!processedUrl) return;
    
    try {
      // 从URL获取图片并下载
      const response = await fetch(processedUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `virtual_staging_result_${taskId}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      setError('Failed to download image');
    }
  };

  const handleDownloadPDF = async () => {
    if (!furnitureList || furnitureList.length === 0) {
      setError('No furniture list available');
      return;
    }
  
    setIsLoading(true);
    setError('');

    try {
      // 动态导入 PDF 库
      const jsPDFModule = await import('jspdf');
      const jsPDF = jsPDFModule.default || jsPDFModule.jsPDF || jsPDFModule;
      
      if (!jsPDF) {
        throw new Error('jsPDF is not available');
      }
      
      // 导入 autoTable 插件
      await import('jspdf-autotable');
      
      // 创建 jsPDF 实例
      let doc = new jsPDF();
      
      // 检查 autoTable 是否可用，如果不可用则手动注册
      if (typeof doc.autoTable === 'undefined') {
        const autoTableModule = await import('jspdf-autotable');
        
        // 使用 applyPlugin 注册插件
        if (autoTableModule.applyPlugin && typeof autoTableModule.applyPlugin === 'function') {
          autoTableModule.applyPlugin(jsPDF);
        } else if (autoTableModule.default && typeof autoTableModule.default === 'function') {
          autoTableModule.default(jsPDF);
        }
        
        // 重新创建文档实例
        doc = new jsPDF();
        
        if (typeof doc.autoTable === 'undefined') {
          throw new Error('autoTable plugin failed to load');
        }
      }
  
      doc.setFontSize(20);
      doc.text('Furniture Purchase List', 105, 20, { align: 'center' });
  
      doc.setFontSize(10);
      doc.text(`Generated: ${new Date().toLocaleDateString()}`, 105, 30, { align: 'center' });
  
      // 预加载所有图片并获取尺寸
      const imageDataMap = {};
      if (Object.keys(furnitureImages).length > 0) {
        for (const furniture of furnitureList) {
          const modelId = furniture.model_id;
          const imageUrl = furnitureImages[modelId];
          if (imageUrl) {
            try {
              const imageData = await loadImageAsBase64(imageUrl);
              // 获取图片尺寸
              const img = new Image();
              await new Promise((resolve, reject) => {
                img.onload = resolve;
                img.onerror = reject;
                img.src = imageData;
              });
              imageDataMap[modelId] = {
                data: imageData,
                width: img.width,
                height: img.height
              };
            } catch (imgError) {
              console.error(`Failed to load image for ${modelId}:`, imgError);
            }
          }
        }
      }
  
      const tableData = furnitureList.map((item, index) => [
        index + 1,
        imageDataMap[item.model_id] || null, // 图片数据（包含 data, width, height）
        item.category || '-',
        item['super-category'] || '-',
        item.style || '-',
        `¥${item.price_cny?.toLocaleString() || '0'}`,
        `${item.xLen || 0}m × ${item.zLen || 0}m`,
        `${item.footprint_m2?.toFixed(2) || '0'} m²`
      ]);
  
      const totalPrice = furnitureList.reduce((sum, item) => sum + (item.price_cny || 0), 0);
      
      // 添加表格，包含图片列
      doc.autoTable({
        startY: 40,
        head: [['#', 'Image', 'Category', 'Type', 'Style', 'Price', 'Size', 'Area']],
        body: tableData,
        theme: 'striped',
        headStyles: { fillColor: [124, 58, 237], textColor: 255 },
        styles: { fontSize: 8 },
        margin: { left: 10, right: 10 },
        columnStyles: {
          0: { cellWidth: 10 }, // #
          1: { cellWidth: 28, cellPadding: 1 }, // Image
          2: { cellWidth: 30 }, // Category
          3: { cellWidth: 26 }, // Type
          4: { cellWidth: 22 }, // Style
          5: { cellWidth: 26, halign: 'right' }, // Price
          6: { cellWidth: 22 }, // Size
          7: { cellWidth: 18, halign: 'right' } // Area
        },
        didParseCell: function(data) {
          // 如果是图片列（第2列，索引为1），不显示文本
          if (data.column.index === 1) {
            if (data.cell.raw && typeof data.cell.raw === 'object') {
              data.cell.text = ''; // 不显示文本
            }
          }
        },
        didDrawCell: function(data) {
          // 如果是图片列（第2列，索引为1）且有图片数据
          if (data.column.index === 1 && data.cell.raw && typeof data.cell.raw === 'object') {
            const imageInfo = data.cell.raw;
            if (imageInfo && imageInfo.data) {
              try {
                // 只在绘制内容时处理（不是表头）
                if (data.row.index === undefined || data.row.index >= 0) {
                  // 获取单元格位置和尺寸
                  const cellX = data.cell.x;
                  const cellY = data.cell.y;
                  const cellWidth = data.cell.width;
                  const cellHeight = data.cell.height;
                  
                  // 计算图片尺寸（保持宽高比，适应单元格）
                  const aspectRatio = imageInfo.width / imageInfo.height;
                  
                  // 留出边距
                  const padding = 2;
                  let imageWidth = cellWidth - padding * 2;
                  let imageHeight = cellHeight - padding * 2;
                  
                  // 根据宽高比调整，确保图片适应单元格
                  if (imageWidth / aspectRatio > imageHeight) {
                    imageWidth = imageHeight * aspectRatio;
                  } else {
                    imageHeight = imageWidth / aspectRatio;
                  }
                  
                  // 居中显示
                  const imageX = cellX + padding + (cellWidth - padding * 2 - imageWidth) / 2;
                  const imageY = cellY + padding + (cellHeight - padding * 2 - imageHeight) / 2;
                  
                  // 确定图片格式
                  const imageFormat = imageInfo.data.startsWith('data:image/jpeg') ? 'JPEG' : 'PNG';
                  
                  // 添加图片
                  doc.addImage(
                    imageInfo.data,
                    imageFormat,
                    imageX,
                    imageY,
                    imageWidth,
                    imageHeight
                  );
                }
              } catch (error) {
                console.error('Error drawing image in cell:', error);
              }
            }
          }
        }
      });
  
      const finalY = doc.lastAutoTable.finalY + 10;
      doc.setFontSize(12);
      doc.setFont(undefined, 'bold');
      doc.text(`Total Price: ¥${totalPrice.toLocaleString()}`, 105, finalY, { align: 'center' });
  
      // 保存PDF
      doc.save(`furniture_list_${taskId}.pdf`);
      setIsLoading(false);
    } catch (error) {
      console.error('PDF generation error:', error);
      console.error('Error details:', {
        errorName: error.name,
        errorMessage: error.message,
        errorStack: error.stack,
        error: error
      });
      
      // 直接显示错误信息，不使用 markdown 兜底
      const errorMessage = `PDF generation failed: ${error.message || error.toString()}`;
      setError(errorMessage);
      
      // 抛出错误以便在控制台看到完整堆栈
      throw error;
    }
  };

  // 加载图片的辅助函数（转换为 base64）
  const loadImageAsBase64 = async (url) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
    } catch (error) {
      console.error('Failed to load image:', error);
      throw error;
    }
  };

  const generateMarkdownList = () => {
    if (!furnitureList || furnitureList.length === 0) return '';
    
    let markdown = '# Furniture Purchase List\n\n';
    markdown += `Generated: ${new Date().toLocaleDateString()}\n\n`;
    markdown += '| # | Category | Type | Style | Price | Size | Area |\n';
    markdown += '|---|----------|------|-------|-------|------|------|\n';
    
    furnitureList.forEach((item, index) => {
      markdown += `| ${index + 1} | ${item.category || '-'} | ${item['super-category'] || '-'} | ${item.style || '-'} | ¥${item.price_cny?.toLocaleString() || '0'} | ${item.xLen || 0}m × ${item.zLen || 0}m | ${item.footprint_m2?.toFixed(2) || '0'} m² |\n`;
    });
    
    const totalPrice = furnitureList.reduce((sum, item) => sum + (item.price_cny || 0), 0);
    markdown += `\n**Total Price: ¥${totalPrice.toLocaleString()}**\n`;
    
    return markdown;
  };

  // Sliding comparison function - Set container size
  useEffect(() => {
    if (!processedUrl || !originalUrl || !comparisonContainerRef.current) return;

    const originalImg = new Image();
    originalImg.src = originalUrl;
    
    originalImg.onload = () => {
      if (comparisonContainerRef.current && comparisonContainerRef.current.parentElement) {
        const aspectRatio = originalImg.naturalHeight / originalImg.naturalWidth;
        const wrapperWidth = comparisonContainerRef.current.parentElement.offsetWidth || comparisonContainerRef.current.parentElement.clientWidth;
        const maxHeight = window.innerHeight * 0.7;
        
        let idealHeight = wrapperWidth * aspectRatio;
        let finalWidth = wrapperWidth;
        let finalHeight = idealHeight;
        
        if (idealHeight > maxHeight) {
          finalHeight = maxHeight;
          finalWidth = maxHeight / aspectRatio;
        }
        
        comparisonContainerRef.current.style.width = `${finalWidth}px`;
        comparisonContainerRef.current.style.height = `${finalHeight}px`;
        comparisonContainerRef.current.style.margin = '0 auto';
      }
    };

    const handleResize = () => {
      if (comparisonContainerRef.current && originalImg.complete && comparisonContainerRef.current.parentElement) {
        const aspectRatio = originalImg.naturalHeight / originalImg.naturalWidth;
        const wrapperWidth = comparisonContainerRef.current.parentElement.offsetWidth || comparisonContainerRef.current.parentElement.clientWidth;
        const maxHeight = window.innerHeight * 0.7;
        
        let idealHeight = wrapperWidth * aspectRatio;
        let finalWidth = wrapperWidth;
        let finalHeight = idealHeight;
        
        if (idealHeight > maxHeight) {
          finalHeight = maxHeight;
          finalWidth = maxHeight / aspectRatio;
        }
        
        comparisonContainerRef.current.style.width = `${finalWidth}px`;
        comparisonContainerRef.current.style.height = `${finalHeight}px`;
        comparisonContainerRef.current.style.margin = '0 auto';
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [originalUrl, processedUrl]);

  // Sliding comparison function - Handle sliding interaction
  useEffect(() => {
    if (!processedUrl || !sliderRef.current || !afterImageRef.current) return;

    const slider = sliderRef.current;
    const afterImage = afterImageRef.current;

    const slideMove = (x) => {
      const containerWidth = slider.parentNode.offsetWidth;
      if (x < 0) x = 0;
      if (x > containerWidth) x = containerWidth;

      slider.style.left = x + 'px';
      const percentage = (x / containerWidth) * 100;
      afterImage.style.clipPath = `polygon(0 0, ${percentage}% 0, ${percentage}% 100%, 0 100%)`;
    };

    const handleMouseDown = (e) => {
      e.preventDefault();
      setIsMoving(true);
    };

    const handleMouseUp = () => {
      setIsMoving(false);
    };

    const handleMouseMove = (e) => {
      if (!isMoving) return;
      let x = e.pageX;
      x -= slider.parentNode.getBoundingClientRect().left;
      slideMove(x);
    };

    const handleTouchStart = (e) => {
      e.preventDefault();
      setIsMoving(true);
    };

    const handleTouchEnd = () => {
      setIsMoving(false);
    };

    const handleTouchMove = (e) => {
      if (!isMoving) return;
      let x;
      if (e.touches) x = e.touches[0].pageX;
      x -= slider.parentNode.getBoundingClientRect().left;
      slideMove(x);
    };

    slider.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mousemove', handleMouseMove);
    slider.addEventListener('touchstart', handleTouchStart);
    document.addEventListener('touchend', handleTouchEnd);
    document.addEventListener('touchmove', handleTouchMove);

    return () => {
      slider.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mousemove', handleMouseMove);
      slider.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchend', handleTouchEnd);
      document.removeEventListener('touchmove', handleTouchMove);
    };
  }, [processedUrl, isMoving]);

  const handleFileSelect = async (file) => {
    if (!file) return;
    if (!selectedModule) {
        setError('Please select a function module first');
      return;
    }

    setIsLoading(true);
    setError('');
    setShowComparison(false);

    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('task_type', selectedModule); // Pass task type

      const response = await fetch(`${API_BASE_URL}/upload-image`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (result.success) {
        // Immediately display the uploaded original image
        setOriginalUrl(`${API_BASE_URL}${result.original_url}`);
        setTaskId(result.task_id); // Save task ID for subsequent processing
        setShowComparison(true);
      } else {
        setError(result.error || 'Upload failed, please try again');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setError('Network error, please check if the backend service is running');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <MandalaBackground />
      
      <div className="app-layout">
        {selectedModule && (
        <Sidebar 
          selectedModule={selectedModule}
          onModuleSelect={handleModuleSelect}
        />
        )}
        
        <div className={`container ${!selectedModule ? 'home-container' : ''}`}>
          <header>
            <div className="header-content">
              <div className="header-text">
                <div className="logo">Virtual Staging System</div>
                <div className="tagline">AI-Powered · Professional Real Estate Marketing Material Creation Platform</div>
              </div>
              {selectedModule && (
                <button className="back-home-btn" onClick={handleBackToHome}>
                  <span className="back-home-icon">🏠</span>
                  <span className="back-home-text">Back to Home</span>
                </button>
              )}
            </div>
          </header>

          {!showComparison && (
          <UploadSection
            onFileSelect={handleFileSelect}
            isVisible={!!selectedModule}
            selectedModule={selectedModule}
          />
          )}

          <ErrorMessage message={error} />

          {showComparison && originalUrl && (
            <div className="uploaded-image-section">
              {processedUrl ? (
                <div className="result-comparison-wrapper">
                  <h3 className="result-title">Processing Result Comparison</h3>
                  <div className="result-comparison-container-wrapper">
                    <div className="result-comparison-container" ref={comparisonContainerRef}>
                      <img
                        className="result-comparison-before"
                        src={originalUrl}
                        alt="Original Image"
                      />
                      <img
                        className="result-comparison-after"
                        ref={afterImageRef}
                        src={processedUrl}
                        alt="Processed Image"
                      />
                      <div className="result-comparison-slider" ref={sliderRef}>
                        <div className="result-comparison-handle"></div>
                      </div>
                    </div>
                  </div>
                  <div className="comparison-hint">Drag the slider to compare before and after</div>
                  
                  {/* Virtual staging furniture list */}
                  {selectedModule === 'virtual' && furnitureList.length > 0 && (
                    <div className="furniture-list-section">
                      <h4 className="furniture-list-title">Selected Furniture</h4>
                      <div className="furniture-grid">
                        {furnitureList.map((furniture, index) => (
                          <div key={index} className="furniture-item">
                            {furnitureImages[furniture.model_id] && (
                              <img 
                                src={furnitureImages[furniture.model_id]} 
                                alt={furniture.category}
                                className="furniture-image"
                              />
                            )}
                            <div className="furniture-info">
                              <div className="furniture-category">{furniture.category}</div>
                              <div className="furniture-super-category">{furniture['super-category']}</div>
                              <div className="furniture-style">Style: {furniture.style}</div>
                              <div className="furniture-price">¥{furniture.price_cny.toLocaleString()}</div>
                              <div className="furniture-size">
                                Size: {furniture.xLen}m × {furniture.zLen}m
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="uploaded-image-container">
                  <img 
                    src={originalUrl} 
                    alt="Uploaded Image" 
                    className="uploaded-image"
                  />
                </div>
              )}
              
              {selectedModule === 'virtual' && !processedUrl && (
                <div className="decoration-options">
                  <div className="option-group">
                    <label className="option-label">Decoration Style</label>
                    <select 
                      className="option-select"
                      value={decorationStyle}
                      onChange={(e) => setDecorationStyle(e.target.value)}
                    >
                      <option value="modern">Modern</option>
                      <option value="chinese">Chinese</option>
                      <option value="minimalist">Minimalist</option>
                      <option value="industrial">Industrial</option>
                      <option value="scandinavian">Scandinavian</option>
                      <option value="classic">Classic</option>
                    </select>
                  </div>
                  
                  <div className="option-group">
                    <label className="option-label">Maximum Budget (CNY)</label>
                    <div className="price-input-group">
                      <input
                        type="range"
                        className="price-slider"
                        min="0"
                        max="50000"
                        step="1000"
                        value={maxPrice}
                        onChange={(e) => setMaxPrice(Number(e.target.value))}
                      />
                      <input
                        type="number"
                        className="price-input"
                        min="0"
                        max="50000"
                        step="1000"
                        value={maxPrice}
                        onChange={(e) => {
                          const value = Number(e.target.value);
                          if (value >= 0 && value <= 50000) {
                            setMaxPrice(value);
                          }
                        }}
                      />
                    </div>
                  </div>
                  
                  <div className="option-group">
                    <label className="option-label">Room Type</label>
                    <select 
                      className="option-select"
                      value={roomType}
                      onChange={(e) => setRoomType(e.target.value)}
                    >
                      <option value="living room">Living Room</option>
                      <option value="bedroom">Bedroom</option>
                      <option value="kitchen">Kitchen</option>
                      <option value="bathroom">Bathroom</option>
                      <option value="dining room">Dining Room</option>
                      <option value="study">Study</option>
                    </select>
                  </div>
                </div>
              )}
              
              <div className="action-buttons">
                {selectedModule === 'denoise' && !processedUrl && (
                  <button className="action-btn process-btn" onClick={handleDenoise}>
                    <span className="action-icon">✨</span>
                    One-Click Clear
                  </button>
                )}
                {selectedModule === 'denoise' && processedUrl && (
                  <>
                    <button className="action-btn download-btn" onClick={handleDownloadImage}>
                      <span className="action-icon">📥</span>
                      One-Click Download
                    </button>
                    <button className="action-btn staging-btn" onClick={handleGoStaging}>
                      <span className="action-icon">🏠</span>
                      Go Staging
                    </button>
                  </>
                )}
                {selectedModule === 'virtual' && !processedUrl && (
                  <button className="action-btn process-btn" onClick={handleVirtualDecorate}>
                    <span className="action-icon">🏠</span>
                    One-Click Decorate
                  </button>
                )}
                {selectedModule === 'virtual' && processedUrl && (
                  <>
                    <button className="action-btn download-btn" onClick={handleDownloadImage}>
                      <span className="action-icon">📥</span>
                      One-Click Download
                    </button>
                    <button className="action-btn purchase-btn" onClick={handleDownloadPDF}>
                      <span className="action-icon">📄</span>
                      One-Click Purchase
                    </button>
                  </>
                )}
                <button className="action-btn reupload-btn" onClick={handleReupload}>
                  <span className="action-icon">🔄</span>
                  Re-upload
                </button>
              </div>
            </div>
          )}

          {!showComparison && !selectedModule && (
            <div className="home-entry">
              <div className="home-hero">
                <h1 className="home-title">Virtual Staging System</h1>
                <p className="home-subtitle">AI-Powered · Professional Real Estate Marketing Material Creation Platform</p>
                <p className="home-description">Intelligent image processing to make your property photos more attractive</p>
              </div>
              
              <div className="home-modules">
                <div 
                  className="home-module-card"
                  onClick={() => handleModuleSelect('denoise')}
                >
                  <div className="home-module-icon">🖼️</div>
                  <h3 className="home-module-title">Clutter Removal</h3>
                  <p className="home-module-desc">Intelligently enhance image quality and remove unwanted objects</p>
                  <div className="home-module-arrow">→</div>
                </div>
                
                <div 
                  className="home-module-card"
                  onClick={() => handleModuleSelect('virtual')}
                >
                  <div className="home-module-icon">🛋️</div>
                  <h3 className="home-module-title">Virtual Staging</h3>
                  <p className="home-module-desc">Add beautiful furniture to empty rooms and showcase potential value</p>
                  <div className="home-module-arrow">→</div>
                </div>
              </div>
            </div>
          )}

          {!showComparison && selectedModule && (
            <>
          <FeaturesSection />
          <TutorialSection />
            </>
          )}
        </div>
      </div>

      <LoadingOverlay isLoading={isLoading} />
    </div>
  );
}

export default App;


