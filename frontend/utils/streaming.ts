/**
 * Utility functions for text streaming
 */

/**
 * Simulates character-by-character text streaming with configurable parameters
 * @param text - The complete text to stream
 * @param updateCallback - Function to call with each chunk of text
 * @param options - Configuration options
 * @returns The complete text once streaming is complete
 */
export const streamText = async (
  text: string,
  updateCallback: (text: string) => void,
  options: {
    chunkSize?: number;      // Number of characters to add per update (default: 1)
    delay?: number;          // Delay between updates in ms (default: 15)
    initialDelay?: number;   // Initial delay before streaming starts (default: 0)
    randomVariation?: boolean; // Add random variation to delay (default: true)
  } = {}
): Promise<string> => {
  // Default options
  const {
    chunkSize = 1,
    delay = 15,
    initialDelay = 0,
    randomVariation = true
  } = options;

  // Wait for initial delay
  if (initialDelay > 0) {
    await new Promise(resolve => setTimeout(resolve, initialDelay));
  }

  let streamedText = '';

  for (let i = 0; i < text.length; i += chunkSize) {
    const chunk = text.slice(i, i + chunkSize);
    streamedText += chunk;
    updateCallback(streamedText);
    
    // Calculate delay with optional random variation
    let currentDelay = delay;
    if (randomVariation) {
      // Add variation between 0.7x and 1.3x
      currentDelay *= 0.7 + Math.random() * 0.6;
      
      // Pause slightly longer at punctuation
      if (['.', '!', '?', ',', ':', ';', '\n'].includes(chunk)) {
        currentDelay *= 2;
      }
    }
    
    await new Promise(resolve => setTimeout(resolve, currentDelay));
  }

  return streamedText;
};

/**
 * Streams text by natural language units (words and punctuation)
 * This provides a more natural reading experience than character-by-character streaming
 */
export const streamTextByWordUnits = async (
  text: string,
  updateCallback: (text: string) => void,
  options: {
    delay?: number;          // Delay between word units in ms (default: 30)
    initialDelay?: number;   // Initial delay before streaming starts (default: 0)
    randomVariation?: boolean; // Add random variation to delay (default: true)
  } = {}
): Promise<string> => {
  // Default options
  const {
    delay = 30,
    initialDelay = 0,
    randomVariation = true
  } = options;

  // Wait for initial delay
  if (initialDelay > 0) {
    await new Promise(resolve => setTimeout(resolve, initialDelay));
  }

  // Calculate base delay based on text length to optimize speed for longer texts
  let baseDelay = delay;
  if (text.length > 500) {
    // Gradually reduce the delay for longer texts
    const lengthFactor = Math.min(text.length / 1000, 3);
    baseDelay = Math.max(delay * (1 - lengthFactor * 0.2), 10);
  }

  // Split text into word units
  const wordUnits = text.match(/\S+\s*|\s+|[.,!?;:]/g) || [];
  let streamedText = '';

  // Use requestAnimationFrame for smoother rendering
  const nextFrame = (callback: () => void) => {
    requestAnimationFrame(() => {
      setTimeout(callback, 0);
    });
  };

  // Process in small batches to prevent UI blocking
  const processBatch = async (startIdx: number, batchSize: number) => {
    const endIdx = Math.min(startIdx + batchSize, wordUnits.length);
    
    for (let i = startIdx; i < endIdx; i++) {
      const unit = wordUnits[i];
      streamedText += unit;
      updateCallback(streamedText);
      
      // Calculate delay with optional random variation
      let currentDelay = baseDelay;
      if (randomVariation) {
        // Add variation between 0.7x and 1.3x
        currentDelay *= 0.7 + Math.random() * 0.6;
        
        // Pause slightly longer at punctuation and new lines
        if (/[.!?]\s*$/.test(unit)) {
          currentDelay *= 3; // End of sentence
        } else if (/[,:;]\s*$/.test(unit)) {
          currentDelay *= 2; // Comma, colon, semicolon
        } else if (/\n/.test(unit)) {
          currentDelay *= 2.5; // New line
        }
      }
      
      await new Promise(resolve => setTimeout(resolve, currentDelay));
    }
    
    // Continue with next batch if there are more units
    if (endIdx < wordUnits.length) {
      return new Promise<void>(resolve => {
        nextFrame(() => {
          processBatch(endIdx, batchSize).then(resolve);
        });
      });
    }
  };

  // Start processing in batches of 10 units
  await processBatch(0, 10);
  
  return streamedText;
}; 