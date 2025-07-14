class ResamplingProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    // Google STT가 요구하는 목표 샘플 레이트는 16kHz입니다.
    this.targetSampleRate = 16000;
    
    // 이 프로세서가 생성될 때의 실제 입력 샘플 레이트입니다. (예: 48000)
    this.inputSampleRate = sampleRate; 
    
    this.resampleRatio = this.inputSampleRate / this.targetSampleRate;
    this.position = 0;
  }

  process(inputs) {
    const inputData = inputs[0][0]; // Float32Array 형식의 오디오 데이터
    
    if (!inputData) {
      return true;
    }
    
    const output = [];
    
    // 입력 데이터를 순회하며, 비율에 맞춰 샘플을 추출합니다.
    while (this.position < inputData.length) {
      output.push(inputData[Math.floor(this.position)]);
      this.position += this.resampleRatio;
    }
    
    // 다음 블록 처리를 위해 현재 블록의 길이를 빼줍니다.
    this.position -= inputData.length;

    if (output.length > 0) {
      // 16-bit PCM 형식으로 변환합니다.
      const int16Array = new Int16Array(output.length);
      for(let i = 0; i < output.length; i++) {
        int16Array[i] = Math.min(1, output[i]) * 0x7FFF;
      }
      
      // 변환된 데이터를 메인 스레드로 보냅니다.
      this.port.postMessage(int16Array.buffer, [int16Array.buffer]);
    }
    
    return true;
  }
}

registerProcessor('resampling-processor', ResamplingProcessor);