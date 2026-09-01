/**
  Copyright (C) 2012-2026 by Autodesk, Inc.
  All rights reserved.

  FANUC post processor configuration.

  $Revision: 44220 2b98af3e523dc041217e3860e4ea3f1fe5d949f9 $
  $Date: 2026-04-01 17:40:42 $

  FORKID {6A0C1F5D-1F55-4900-A38E-4C7292F5FD89}
*/

description = "Matsuura";
vendor = "Matsuura";
vendorUrl = "http://www.matsuura.co.jp";
legal = "Copyright (C) 2012-2026 by Autodesk, Inc.";
certificationLevel = 2;
minimumRevision = 45917;

longDescription = "5-axis base post for Matsuura Mills with a FANUC control.";

extension = "nc";
programNameIsInteger = true;
setCodePage("ascii");

capabilities = CAPABILITY_MILLING | CAPABILITY_MACHINE_SIMULATION;
tolerance = spatial(0.002, MM);
if (typeof revision == "number" && typeof supportedFeatures != "undefined") {
  supportedFeatures |= revision >= 50328 ? FEATURE_MACHINE_ROTARY_ANGLES : 0;
}

minimumChordLength = spatial(0.25, MM);
minimumCircularRadius = spatial(0.01, MM);
maximumCircularRadius = spatial(1000, MM);
minimumCircularSweep = toRad(0.01);
maximumCircularSweep = toRad(180);
allowHelicalMoves = true;
allowedCircularPlanes = undefined; // allow any circular motion
highFeedrate = (unit == MM) ? 5000 : 200;
probeMultipleFeatures = true;

// user-defined properties
properties = {
  preloadTool: {
    title      : "Preload tool",
    description: "Preloads the next tool at a tool change (if any). TH: โหลดดอกถัดไปล่วงหน้าตอนเปลี่ยนดอก ถ้าไม่มีดอกถัดไปจะไม่ทำอะไร.",
    group      : "preferences",
    type       : "boolean",
    value      : true,
    visible    : false,
    scope      : "post"
  },
  showSequenceNumbers: {
    title      : "Use sequence numbers",
    description: "'Yes' outputs sequence numbers on each block, 'Only on tool change' outputs sequence numbers on tool change blocks only, and 'No' disables the output of sequence numbers. TH: เลือกว่าจะใส่เลข N หน้าแต่ละบรรทัดหรือไม่.",
    group      : "formats",
    type       : "enum",
    values     : [
      {title:"Yes", id:"true"},
      {title:"No", id:"false"},
      {title:"Only on tool change", id:"toolChange"}
    ],
    value: "true",
    scope: "post"
  },
  sequenceNumberStart: {
    title      : "Start sequence number",
    description: "The number at which to start the sequence numbers. TH: เลข N เริ่มต้นของโปรแกรม เช่น 10.",
    group      : "formats",
    type       : "integer",
    value      : 10,
    scope      : "post"
  },
  sequenceNumberIncrement: {
    title      : "Sequence number increment",
    description: "The amount by which the sequence number is incremented by in each block. TH: ระยะเพิ่มของเลข N ในแต่ละบรรทัด เช่น เพิ่มทีละ 5.",
    group      : "formats",
    type       : "integer",
    value      : 5,
    scope      : "post"
  },
  optionalStop: {
    title      : "Optional stop",
    description: "Outputs optional stop code during when necessary in the code. TH: ใส่ M01 หยุดแบบ optional ในจุดที่เหมาะสม.",
    group      : "preferences",
    type       : "boolean",
    value      : true,
    scope      : "post"
  },
  o8: {
    title      : "8 Digit program number",
    description: "Specifies that an 8 digit program number is needed. TH: ใช้เลขโปรแกรมแบบ 8 หลัก เฉพาะกรณีที่เครื่อง/งานต้องการ.",
    group      : "formats",
    type       : "boolean",
    value      : false,
    scope      : "post"
  },
  separateWordsWithSpace: {
    title      : "Separate words with space",
    description: "Adds spaces between words if 'yes' is selected. TH: ใส่ช่องว่างระหว่างคำสั่ง G-code เพื่อให้อ่านง่าย.",
    group      : "formats",
    type       : "boolean",
    value      : true,
    scope      : "post"
  },
  allow3DArcs: {
    title      : "Allow 3D arcs",
    description: "Specifies whether 3D circular arcs are allowed. TH: อนุญาต arc แบบ 3D ถ้าไม่แน่ใจให้ปิดไว้.",
    group      : "preferences",
    type       : "boolean",
    value      : false,
    scope      : "post"
  },
  useRadius: {
    title      : "Radius arcs",
    description: "If yes is selected, arcs are outputted using radius values rather than IJK. TH: ให้ arc ใช้ค่า R แทน IJK.",
    group      : "preferences",
    type       : "boolean",
    value      : false,
    visible    : false,
    scope      : "post"
  },
  forceIJK: {
    title      : "Force IJK",
    description: "Force the output of IJK for G2/G3 when not using R mode. TH: บังคับให้ G2/G3 ใช้ IJK เมื่อไม่ได้ใช้ R.",
    group      : "preferences",
    type       : "boolean",
    value      : false,
    visible    : false,
    scope      : "post"
  },
  showNotes: {
    title      : "Show notes",
    description: "Writes operation notes as comments in the outputted code. TH: ใส่ note ของ operation เป็น comment ใน NC.",
    group      : "formats",
    type       : "boolean",
    value      : false,
    scope      : "post"
  },
  useSmoothing: {
    title      : "Use smoothing",
    description: "Specifies if smoothing should be used or not. TH: เปิด/ปิดโหมด smoothing หลักของเครื่อง ค่า Automatic ให้ post เลือกตามชนิดงาน.",
    group      : "preferences",
    type       : "enum",
    values     : [
      {title:"No", id:"-1"},
      {title:"Automatic", id:"9999"},
      {title:"Rough", id:"1"},
      {title:"Semi", id:"2"},
      {title:"Finish", id:"3"}
    ],
    value: "9999",
    scope: ["post"/*,"operation"*/]
  },
  tcpSmoothingLevel: {
    title      : "TCP smoothing level",
    description: "Overrides G131 F-level smoothing for G43.4 TCP sections. Default F3 is the field-proven finish baseline; Automatic keeps the operation-driven post level. TH: ระดับ G131 F สำหรับงาน TCP/G43.4 ค่าเริ่มต้น F3 คือค่าที่ทดสอบแล้ว ถ้าเลือก Automatic จะให้ post เลือกตาม operation.",
    group      : "multiAxis",
    type       : "enum",
    values     : [
      {title:"Automatic F-level", id:"auto"},
      {title:"No", id:"-1"},
      {title:"F1 Rough / Speed", id:"1"},
      {title:"F2 Semi", id:"2"},
      {title:"F3 Finish", id:"3"}
    ],
    value      : "3",
    scope      : "post"
  },
  tcpMaximumCuttingFeed: {
    title      : "TCP max cutting feed",
    description: "Optional feed cap for simultaneous G43.4 TCP cutting moves. 0 keeps the CAM feed. TH: จำกัด feed สูงสุดเฉพาะตอนกัด TCP 5 แกนพร้อมกัน ใส่ 0 คือใช้ feed จาก CAM.",
    group      : "multiAxis",
    type       : "integer",
    value      : 0,
    scope      : "post"
  },
  tcpRotaryLimiterFeed: {
    title      : "TCP rotary limiter feed",
    description: "Experimental G94 feed used only when TCP cutting has very short XYZ motion with a large B/C angle change. 0 disables this limiter. TH: โหมดทดสอบ ลด feed เฉพาะบล็อก TCP ที่ XYZ เดินสั้นมากแต่ B/C หมุนเยอะ ใส่ 0 คือปิด.",
    group      : "multiAxis",
    type       : "integer",
    value      : 0,
    visible    : false,
    scope      : "post"
  },
  tcpRotaryLimiterMaxXYZMicrons: {
    title      : "TCP rotary limiter XYZ um",
    description: "XYZ chord threshold in microns for the TCP rotary limiter. The limiter can act only when XYZ travel is at or below this value. TH: ระยะ XYZ ต่อบล็อกเป็นไมครอน ถ้าเดินสั้นกว่าค่านี้และ B/C หมุนเยอะ จะลด feed.",
    group      : "multiAxis",
    type       : "integer",
    value      : 50,
    visible    : false,
    scope      : "post"
  },
  tcpRotaryLimiterMinAngle: {
    title      : "TCP rotary limiter angle deg",
    description: "Minimum B/C angle change in degrees that can trigger the TCP rotary feed limiter. TH: องศา B/C ขั้นต่ำต่อบล็อกที่จะเริ่มลด feed แนะนำเริ่มที่ 1 องศา.",
    group      : "multiAxis",
    type       : "integer",
    value      : 1,
    visible    : false,
    scope      : "post"
  },
  tcpRotaryMaxDegreesPerMinute: {
    title      : "TCP rotary max deg/min",
    description: "G94 feed limiter based on B/C angular speed. Default 1000 is the field-proven severe C-axis jerk baseline; 0 disables this limiter. TH: จำกัดความเร็วหมุน B/C เป็นองศาต่อนาที ค่าเริ่มต้น 1000 คือค่าที่ทดสอบแล้วสำหรับอาการ C กระตุกหนัก ใส่ 0 คือปิด.",
    group      : "multiAxis",
    type       : "integer",
    value      : 1000,
    scope      : "post"
  },
  tcpRotaryRapidFeed: {
    title      : "TCP rotary rapid feed",
    description: "Feed for TCP rapid reposition moves that include B/C motion. Default 800 is the field-proven severe C-axis jerk baseline; 0 keeps normal G00 rapid. TH: เปลี่ยน G00 ที่มี B/C ตอนเปิด TCP ให้เป็น G01 ด้วย feed นี้ ค่าเริ่มต้น 800 คือค่าที่ทดสอบแล้ว ใส่ 0 คือใช้ G00 เดิม.",
    group      : "multiAxis",
    type       : "integer",
    value      : 800,
    scope      : "post"
  },
  tcpFeedMode: {
    title      : "TCP feed mode",
    description: "Feed output for G43.4 TCP sections. G94 feed/min is the only production-proven mode for this machine; G93 inverse time alarmed 010 and is disabled. TH: วิธีป้อน feed สำหรับ TCP/G43.4 เครื่องนี้ใช้ G94 เท่านั้นในงานจริง เพราะ G93 เคย alarm 010.",
    group      : "multiAxis",
    type       : "enum",
    values     : [
      {title:"G94 feed/min - proven", id:"g94"}
    ],
    value      : "g94",
    visible    : false,
    scope      : "post"
  },
  usePitchForTapping: {
    title      : "Use pitch for tapping",
    description: "Enables the use of pitch instead of feed for the F-word in canned tapping cycles. Your CNC control must be setup for pitch mode! TH: ใช้ pitch แทน feed ในงาน tap เฉพาะกรณีที่ control ตั้งไว้รองรับ.",
    group      : "preferences",
    type       : "boolean",
    value      : false,
    visible    : false,
    scope      : "post"
  },
  useG95: {
    title      : "Use G95",
    description: "Use IPR/MPR instead of IPM/MPM. TH: ใช้ feed ต่อรอบแทน feed ต่อนาที ถ้าไม่ต้องการให้ใช้ค่าปกติ.",
    group      : "preferences",
    type       : "boolean",
    value      : false,
    visible    : false,
    scope      : "post"
  },
  allowDrillingCannedCyclesProof: {
    title      : "Use drill canned cycles (G81/G83)",
    description: "Production default after 5011 machine proof. Outputs normal drilling, counter-boring, chip-breaking, and deep-drilling as canned cycles instead of expanded G00/G01 moves. Set No only to force expanded fallback output. TH: เปิดให้เจาะออกเป็น cycle G81/G83 แบบปกติ ซึ่งทดสอบกับเครื่องแล้ว ถ้าต้องการบังคับให้แตกเป็น G00/G01 ค่อยตั้งเป็น No.",
    group      : "preferences",
    type       : "boolean",
    value      : true,
    scope      : "post"
  },
  matsuuraToolLengthSetMode: {
    title      : "Tool length set mode",
    description: "Outputs Matsuura tool length setting calls. Off leaves NC output unchanged. Use only after tool setter setup is verified. TH: โหมดตั้งความยาวดอกอัตโนมัติ ถ้าเลือก Off โปรแกรมจะเหมือนเดิม ใช้เฉพาะเมื่อมั่นใจว่า tool setter พร้อมแล้ว.",
    group      : "preferences",
    type       : "enum",
    values     : [
      {title:"Off", id:"off"},
      {title:"All tools at program start", id:"allAtProgramStart"},
      {title:"Before first use", id:"beforeFirstUse"},
      {title:"Every tool change", id:"everyToolChange"}
    ],
    value      : "off",
    scope      : "post"
  },
  matsuuraToolLengthSetCycle: {
    title      : "Tool length set cycle",
    description: "Normal O9303 is the proven unknown-tool cycle. Fast rough-H O1938 uses the current rough H for a faster approach and requires O1938 loaded in CNC memory plus a trusted rough H. TH: เลือก macro ตั้งความยาวดอก O9303 ใช้กับดอกที่ยังไม่รู้ H ส่วน O1938 เร็วกว่าแต่ต้องมี H คร่าว ๆ ที่เชื่อถือได้และโหลด O1938 ไว้ในเครื่อง.",
    group      : "preferences",
    type       : "enum",
    values     : [
      {title:"Normal O9303", id:"normalO9303"},
      {title:"Fast rough-H O1938", id:"fastRoughHO1938"}
    ],
    value      : "fastRoughHO1938",
    scope      : "post"
  },
  matsuuraToolBreakageCheckMode: {
    title      : "Tool breakage check mode",
    description: "Outputs Matsuura O9301 breakage-check calls using the current H offset as the reference. Off leaves NC output unchanged. TH: โหมดเช็คดอกหักก่อนกัด ใช้ O9301 เทียบกับค่า H ปัจจุบัน ถ้า Off โปรแกรมจะไม่เพิ่มการเช็ค.",
    group      : "preferences",
    type       : "enum",
    values     : [
      {title:"Off", id:"off"},
      {title:"All tools at program start", id:"allAtProgramStart"},
      {title:"Before first use", id:"beforeFirstUse"},
      {title:"Every tool change", id:"everyToolChange"}
    ],
    value      : "off",
    scope      : "post"
  },
  matsuuraToolBreakageAction: {
    title      : "Broken tool action",
    description: "Alarm/stop keeps the proven O9301 M0 behavior. Try sister tool calls O1939/O9999 for pre-cut recovery, and O1940 for post-cut sister recovery with rerun. TH: เลือกว่าจะทำอะไรเมื่อเจอดอกหัก Alarm/stop คือหยุดเตือนแบบเดิม ส่วน Try sister tool คือพยายามเรียกดอกสำรองตาม Tool Manager.",
    group      : "preferences",
    type       : "enum",
    values     : [
      {title:"Alarm/stop", id:"alarmStop"},
      {title:"Try sister tool", id:"trySisterTool"}
    ],
    value      : "alarmStop",
    scope      : "post"
  },
  matsuuraToolBreakagePostCutMode: {
    title      : "Post-cut tool breakage check mode",
    description: "Outputs Matsuura breakage checks after cutting. After each tool run checks when the tool is finished, before the next tool; with sister recovery it reruns that whole tool run. TH: เช็คดอกหลังจากกัดเสร็จ แนะนำ After each tool run คือเช็คเมื่อดอกนั้นทำงานครบแล้ว ถ้าหักและใช้ดอกสำรอง จะกลับไปกัดช่วงของดอกนั้นซ้ำ.",
    group      : "preferences",
    type       : "enum",
    values     : [
      {title:"Off", id:"off"},
      {title:"After each tool run", id:"afterToolRun"},
      {title:"After each operation", id:"afterEachOperation"}
    ],
    value      : "off",
    scope      : "post"
  },
  matsuuraPostCutRerunOutputMode: {
    title      : "Post-cut sister rerun output",
    description: "Single memory program keeps the earlier memory-only IF/GOTO output. Hybrid writes a small memory scheduler plus CF tool-run files named O#### with no extension. TH: วิธีออกโปรแกรมสำหรับเช็คหลังกัดแล้วใช้ดอกสำรอง แบบ Single เป็นไฟล์เดียวใน memory ส่วน Hybrid จะได้ main ไว้โหลดเข้าเครื่อง และไฟล์ O#### ไว้ใส่ CF.",
    group      : "preferences",
    type       : "enum",
    values     : [
      {title:"Single memory program", id:"memorySingle"},
      {title:"Hybrid memory main + CF tool files", id:"hybridMemoryCf"}
    ],
    value      : "memorySingle",
    scope      : "post"
  },
  matsuuraHybridToolRunFirstProgram: {
    title      : "CF tool-run first O-number",
    description: "Hybrid output only. First generated CF tool-run file is O#### with no extension; later tool runs increment from this number. TH: ใช้กับ Hybrid เท่านั้น เป็นเลข O เริ่มต้นของไฟล์ย่อยบน CF เช่น 3001 แล้วไฟล์ต่อไปจะเป็น 3002, 3003.",
    group      : "preferences",
    type       : "integer",
    value      : 3001,
    scope      : "post"
  },
  matsuuraToolBreakageTolerance: {
    title      : "Tool breakage tolerance D",
    description: "Allowed H-length difference for O9301 tool breakage checks. Default D0.5 keeps the original behavior; use a smaller value for critical jobs. TH: ค่าคลาดเคลื่อนที่ยอมให้ตอนเช็คดอกหัก ค่าเดิม D0.5 ถ้างานสำคัญมากอาจลดค่านี้ได้.",
    group      : "preferences",
    type       : "number",
    value      : 0.5,
    scope      : "post"
  },
  matsuuraToolOffsetSource: {
    title      : "Tool offset source",
    description: "Fusion fixed H/D keeps normal output. Matsuura selected-pot variables outputs H#518 and D#517 after M6, for proven Tool Manage duplicate T-NO/SEL sister tools. TH: เลือกแหล่งค่า H/D แบบ Fusion fixed คือค่าเดิมจาก Fusion ส่วน Matsuura selected-pot ใช้ #518/#517 ตามดอกจริงที่ Tool Manager เลือกหลัง M6.",
    group      : "preferences",
    type       : "enum",
    values     : [
      {title:"Fusion fixed H/D", id:"fusionFixed"},
      {title:"Matsuura selected pot #518/#517", id:"matsuuraSelectedPotVariables"}
    ],
    value      : "fusionFixed",
    scope      : "post"
  },
  matsuuraPalletOutputMode: {
    title      : "Pallet / APC output mode",
    description: "Off keeps normal output unchanged. Memory loader + CF body writes two files and keeps its recorded O0001 schedule return. Direct DATA_SV schedule writes one complete work program for Pallet Manager/Data Server and returns to machine-passed CNC-memory O6597 with M98. TH: Off คงโปรแกรมปกติเดิม แบบ Memory loader + CF body สร้างสองไฟล์และยังกลับ O0001 ตามเส้นทางเดิม ส่วน Direct DATA_SV schedule สร้างโปรแกรมงานไฟล์เดียวและกลับ O6597 ใน CNC memory ด้วย M98.",
    group      : "preferences",
    type       : "enum",
    values     : [
      {title:"Off - normal program", id:"off"},
      {title:"Memory loader + CF work body", id:"cfBody"},
      {title:"Direct DATA_SV schedule program", id:"dataServerSchedule"}
    ],
    value      : "off",
    scope      : "post"
  },
  matsuuraPalletCfBodyProgram: {
    title      : "Pallet CF body O-number",
    description: "Used only by Memory loader + CF body. Creates external O#### with no extension; this number must match the Fusion NC Program number. Direct DATA_SV schedule ignores this value. TH: ใช้เฉพาะแบบ Memory loader + CF body เพื่อสร้างไฟล์ O#### ไม่มีนามสกุล โดยเลขต้องตรงกับ NC Program ใน Fusion; แบบ Direct DATA_SV schedule จะไม่ใช้ค่านี้.",
    group      : "preferences",
    type       : "integer",
    value      : 3601,
    scope      : "post"
  },
  matsuuraPalletLoaderFinish: {
    title      : "Pallet CF memory-loader finish",
    description: "Used only by Memory loader + CF body. Single pallet ends the memory loader with M30; Schedule auto returns it to shared O0001. Direct DATA_SV schedule ignores this selector and returns its one complete work program to fixed O6597. TH: ใช้เฉพาะแบบ Memory loader + CF body โดย Single pallet จบ loader ด้วย M30 และ Schedule auto กลับ O0001; แบบ Direct DATA_SV schedule ไม่ใช้ตัวเลือกนี้และกลับ O6597.",
    group      : "preferences",
    type       : "enum",
    values     : [
      {title:"Single pallet - M30", id:"singleM30"},
      {title:"Schedule auto - return to Start Program", id:"scheduleReturn"}
    ],
    value      : "singleM30",
    scope      : "post"
  },
  matsuuraPalletStartProgram: {
    title      : "CF schedule Start Program O-number (fixed O1)",
    description: "Used only by Memory loader + CF body Schedule auto. Output is forced to recorded O0001; stale cached values such as physical pallet 3/5 are ignored with a warning. Direct DATA_SV schedule ignores this value and uses fixed machine-passed O6597. TH: ใช้เฉพาะ Schedule auto ของ Memory loader + CF body และบังคับเป็น O0001; Direct DATA_SV schedule ไม่ใช้ค่านี้และกลับ O6597.",
    group      : "preferences",
    type       : "integer",
    value      : 1,
    scope      : "post"
  },
  matsuuraPalletCfApcInspectionProof: {
    title      : "CF-body APC inspection pair (proof)",
    description: "Default Off preserves the proven Pallet CF guard. Enable only for a matched APC_EXCHANGE out/return pair inside a memory-loader-called CF body; no machining may run while the original pallet is away. TH: ค่าเริ่มต้น Off จะคงตัวกันเดิม เปิดเฉพาะการทดลองใช้ APC_EXCHANGE เป็นคู่เอาพาเลทออกตรวจและเรียกกลับภายใน CF body ที่ถูกเรียกจากโปรแกรมใน memory โดยห้ามตัดงานขณะที่พาเลทเดิมยังไม่กลับ.",
    group      : "preferences",
    type       : "boolean",
    value      : false,
    scope      : "post"
  },
  matsuuraCfCardSafeOutput: {
    title      : "CF card safe output",
    description: "Yes stops posting when known options could output unsafe CF-main control flow. Hybrid post-cut rerun is allowed because the scheduler main must be loaded in CNC memory and only tool-run files live on CF. TH: เปิดไว้เพื่อกันโปรแกรมที่ไม่เหมาะกับการรันตรงจาก CF ถ้าใช้ Hybrid ให้โหลด main เข้า memory และเอาไฟล์ O#### ไว้ใน CF.",
    group      : "preferences",
    type       : "boolean",
    value      : true,
    visible    : true,
    scope      : "post"
  },
  matsuuraApcEndExchange: {
    title      : "End-of-job APC exchange",
    description: "Outputs the field-proven Matsuura APC end exchange sequence before M30. Default Off leaves NC output unchanged. Use only after pallet state is verified. TH: สั่งเปลี่ยนพาเลทท้ายงานก่อน M30 ค่า Off คือไม่เพิ่มอะไร ใช้เฉพาะเมื่อเช็คสถานะพาเลทพร้อมแล้ว.",
    group      : "preferences",
    type       : "boolean",
    value      : false,
    scope      : "post"
  },
  matsuuraFinalMultiTurnCReturn: {
    title      : "Multi-turn C reference return (proof)",
    description: "Uses the Matsuura reference-return path instead of an absolute multi-turn C0 move at guarded neutral TCP entries, TCP-to-indexed section entries, and final closeout when |C| is greater than 360 degrees. Default Off preserves current NC. Supported with End-of-job APC exchange only as a guarded proof path. Not supported with intermediate APC_EXCHANGE, pallet CF, or tailstock until separately proven. TH: ใช้การกลับจุดอ้างอิงของ Matsuura แทนการสั่ง C0 แบบ absolute หลายรอบ ณ จุดเข้า TCP ที่เป็นกลาง, จุดเปลี่ยนจาก TCP ไปงาน indexed และช่วงปิดงาน เมื่อ |C| มากกว่า 360 องศา ค่าเริ่มต้น Off ใช้ร่วมกับ End-of-job APC exchange ได้เฉพาะเส้นทางทดสอบที่มีการป้องกัน และยังไม่รองรับ APC_EXCHANGE กลางโปรแกรม, pallet CF หรือ tailstock จนกว่าจะพิสูจน์แยก.",
    group      : "preferences",
    type       : "boolean",
    value      : false,
    scope      : "post"
  },
  useG54x4: {
    title      : "Use G54.4",
    description: "Fanuc 30i supports G54.4 for workpiece error compensation. TH: ใช้ G54.4 สำหรับชดเชยความคลาดเคลื่อนชิ้นงาน ถ้าไม่ใช้งาน probe/compensation ให้ปิดไว้.",
    group      : "probing",
    type       : "boolean",
    value      : false,
    visible    : false,
    scope      : "post"
  },
  safeStartAllOperations: {
    title      : "Safe start all operations",
    description: "Write optional blocks at the beginning of all operations that include all commands to start program. TH: ใส่บรรทัดเริ่มต้นแบบปลอดภัยทุก operation ทำให้โปรแกรมยาวขึ้น.",
    group      : "preferences",
    type       : "boolean",
    value      : false,
    visible    : false,
    scope      : "post"
  },
  safePositionMethod: {
    title      : "Safe Retracts",
    description: "Select your desired retract option. 'Clearance Height' retracts to the operation clearance height. TH: วิธีถอยแกนกลับตำแหน่งปลอดภัย ปัจจุบันใช้ G53 ตาม workflow เครื่องนี้.",
    group      : "homePositions",
    type       : "enum",
    values     : [
      {title:"G28", id:"G28"},
      {title:"G53", id:"G53"}
      // {title: "Clearance Height", id: "clearanceHeight"}
    ],
    value: "G53",
    scope: "post"
  },
  useRigidTapping: {
    title      : "Use rigid tapping",
    description: "Select 'Yes' to enable Matsuura rigid tapping with M80 S before G84/G74. Rigid tapping does not output an M03/M04 spindle-start block. TH: เปิด rigid tap ของ Matsuura โดยใช้ M80 S ก่อน G84/G74 และไม่สั่ง M03/M04 ก่อน tap.",
    group      : "preferences",
    type       : "enum",
    values     : [
      {title:"Yes", id:"yes"},
      {title:"No", id:"no"},
      {title:"Without spindle direction", id:"without"}
    ],
    value: "yes",
    visible: false,
    scope: "post"
  },
  useTiltedWorkplane: {
    title      : "Workplane output",
    description: "Automatic outputs G68.2/G53.1 for indexed 3+2 sections and neutral-entry G43.4 TCP for 4/5-axis sections. Force TCP uses G43.4 for tilted/indexed sections too. TH: เลือก logic การเอียงงาน Auto คือ 3+2 ใช้ TWP และ 4/5 แกนใช้ TCP ตามที่เราพิสูจน์แล้ว.",
    group      : "multiAxis",
    type       : "enum",
    values     : [
      {title:"Automatic", id:"auto"},
      {title:"Force TCP G43.4", id:"tcp"},
      {title:"Force indexed G68.2", id:"twp"},
      {title:"Force rotary angles", id:"rotary"}
    ],
    value      : "auto",
    visible    : false,
    scope      : ["post"/*,"machine"*/]
  },
  useABCPrepositioning: {
    title      : "Preposition rotaries",
    description: "Enable to preposition rotary axes prior to G68.2 blocks. TH: ให้หมุน B/C ไปตำแหน่งก่อนเปิด G68.2 ใช้กับงาน TWP 3+2.",
    group      : "multiAxis",
    type       : "boolean",
    value      : true,
    visible    : false,
    scope      : ["post"/*,"machine"*/]
  },
  rotaryAxesClampCodes: {
    title      : "Rotary axes clamp codes",
    description: "Specifies the clamp codes for the rotary axes. TH: เลือก M-code สำหรับ clamp/unclamp แกนหมุน เครื่องเราปกติใช้ M131/M132.",
    group      : "multiAxis",
    type       : "enum",
    values     : [
      {title:"M131/M132", id:"1"},
      {title:"M21/M22", id:"2"},
    ],
    value: "1",
    visible: false,
    scope: "post"
  },
  clampBForCAxisTCP: {
    title      : "Clamp B for C-axis TCP",
    description: "Clamp B with M21 and keep C unclamped with M24 for TCP sections where B is fixed and C rotates. TH: สำหรับงาน C-live ให้ B อยู่คงที่แล้ว clamp B ด้วย M21 และปล่อย C หมุนด้วย M24.",
    group      : "multiAxis",
    type       : "boolean",
    value      : true,
    visible    : false,
    scope      : "post"
  },
  singleResultsFile: {
    title      : "Create single results file",
    description: "Set to false if you want to store the measurement results for each probe / inspection toolpath in a separate file. TH: รวมผล probe/inspection ไว้ไฟล์เดียว ถ้าปิดจะแยกไฟล์ตาม toolpath.",
    group      : "probing",
    type       : "boolean",
    value      : true,
    visible    : false,
    scope      : "post"
  },
  probingMacros: {
    title      : "Probing macros",
    description: "Matsuura MAM72/G-Tech 30i uses the proven O82xx/O84xx probing macro family. Legacy Renishaw/PQI cached values are accepted only so old NC programs open; output is still forced to Matsuura. TH: เครื่องนี้ใช้ macro probe ตระกูล O82xx/O84xx ของ Matsuura ค่า Renishaw/PQI เก่าแค่กันไฟล์เก่าเปิดไม่ได้ แต่ output ยังเป็น Matsuura.",
    group      : "probing",
    type       : "enum",
    values     : [
      {title:"Matsuura O82xx/O84xx", id:"matsuura"},
      {title:"Matsuura O82xx/O84xx (legacy Renishaw cache)", id:"renishaw"},
      {title:"Matsuura O82xx/O84xx (legacy PQI cache)", id:"inspectSurface"}
    ],
    value: "matsuura",
    visible: false,
    scope: "post"
  },
  matsuuraProbeApproachDistanceOverride: {
    title      : "Matsuura probe approach override #504",
    description: "Manual override for #504. Leave 0 to output Fusion probe overtravel. This uses a new property id so stale cached 5 mm values are ignored. TH: ตั้งค่า #504 เองสำหรับระยะค้นหา probe ถ้าใส่ 0 จะใช้ค่าจาก Fusion และไม่เอาค่า cache เก่า 5 mm มาใช้.",
    group      : "probing",
    type       : "number",
    value      : 0,
    visible    : false,
    scope      : "post"
  },
  matsuuraProbeMeasureFeedOverride: {
    title      : "Matsuura probe measure feed override #505",
    description: "Manual override for #505. Leave 0 to output Fusion Measure Feedrate, falling back to Fusion cycle measure/feedrate values. This uses a new property id so stale cached 30 mm/min values are ignored. TH: ตั้ง feed ตอน probe วัดจริง #505 เอง ถ้าใส่ 0 จะใช้ Measure Feedrate จาก Fusion และไม่เอาค่า cache เก่า 30 mm/min มาใช้.",
    group      : "probing",
    type       : "number",
    value      : 0,
    visible    : false,
    scope      : "post"
  },
  matsuuraProbeFastFeedOverride: {
    title      : "Matsuura probe fast feed override #506",
    description: "Manual override for #506. Leave 0 to output Fusion Lead-In Feedrate, falling back to Fusion high/feedrate values. This uses a new property id so stale cached 500 mm/min values are ignored. TH: ตั้ง feed เดินเข้าเร็วของ probe #506 เอง ถ้าใส่ 0 จะใช้ Lead-In Feedrate จาก Fusion และไม่เอาค่า cache เก่า 500 mm/min มาใช้.",
    group      : "probing",
    type       : "number",
    value      : 0,
    visible    : false,
    scope      : "post"
  },
  matsuuraProbeDiameter: {
    title      : "Matsuura probe diameter #508",
    description: "Probe ball diameter for Matsuura O82xx/O84xx probing macros. Use 0 to output the Fusion probe tool diameter. TH: เส้นผ่านศูนย์กลางลูก probe สำหรับ macro Matsuura ถ้าใส่ 0 จะใช้ขนาด probe จาก Fusion.",
    group      : "probing",
    type       : "number",
    value      : 0,
    scope      : "post"
  },
  matsuuraProbeResultNumber: {
    title      : "Matsuura probe result A",
    description: "A argument for Matsuura probing result history. Default A91 matches the proven rectangular outside wrapper style. TH: ค่า A สำหรับบันทึกผล probe ของ Matsuura ค่าเริ่มต้น A91 ใช้ตามแบบที่ทดสอบกับ wrapper แล้ว.",
    group      : "probing",
    type       : "number",
    value      : 91,
    visible    : false,
    scope: "post"
  }
};

// wcs definiton
wcsDefinitions = {
  useZeroOffset: false,
  wcs          : [
    {name:"Standard", format:"G", range:[54, 59]},
    {name:"Extended", format:"G54.1 P", range:[1, 300]}
  ]
};

var gFormat = createFormat({prefix:"G", minDigitsLeft:2, decimals:1});
var mFormat = createFormat({prefix:"M", minDigitsLeft:2, decimals:1});
var hFormat = createFormat({prefix:"H", minDigitsLeft:2, decimals:1});
var diameterOffsetFormat = createFormat({prefix:"D", minDigitsLeft:2, decimals:1});
var probeWCSFormat = createFormat({prefix:"S", decimals:0, type:FORMAT_REAL});
var probeExtWCSFormat = createFormat({prefix:"S", decimals:0, type:FORMAT_REAL, offset:100});

var xyzFormat = createFormat({decimals:(unit == MM ? 3 : 4), type:FORMAT_REAL});
var ijkFormat = createFormat({decimals:6, type:FORMAT_REAL}); // unitless
var rFormat = xyzFormat; // radius
var abcFormat = createFormat({decimals:3, type:FORMAT_REAL, scale:DEG});
var feedFormat = createFormat({decimals:(unit == MM ? 0 : 1), type:FORMAT_REAL});
var inverseTimeFormat = createFormat({decimals:3, type:FORMAT_REAL});
var pitchFormat = createFormat({decimals:(unit == MM ? 3 : 4), type:FORMAT_REAL});
var toolFormat = createFormat({decimals:0});
var rpmFormat = createFormat({decimals:0});
var secFormat = createFormat({decimals:3, type:FORMAT_REAL}); // seconds - range 0.001-99999.999
var milliFormat = createFormat({decimals:0}); // milliseconds // range 1-9999
var taperFormat = createFormat({decimals:1, scale:DEG});
var oFormat = createFormat({minDigitsLeft:4, decimals:0});
var matsuuraPalletOFormat = createFormat({minDigitsLeft:4, decimals:0});
var peckFormat = createFormat({decimals:(unit == MM ? 3 : 4), type:FORMAT_REAL});
// var peckFormat = createFormat({decimals:0, type:FORMAT_LZS, minDigitsLeft:4, scale:(unit == MM ? 1000 : 10000)});

var xOutput = createOutputVariable({onchange:function() {state.retractedX = false;}, prefix:"X"}, xyzFormat);
var yOutput = createOutputVariable({onchange:function() {state.retractedY = false;}, prefix:"Y"}, xyzFormat);
var zOutput = createOutputVariable({onchange:function() {state.retractedZ = false;}, prefix:"Z"}, xyzFormat);
var toolVectorOutputI = createOutputVariable({prefix:"I", control:CONTROL_FORCE}, ijkFormat);
var toolVectorOutputJ = createOutputVariable({prefix:"J", control:CONTROL_FORCE}, ijkFormat);
var toolVectorOutputK = createOutputVariable({prefix:"K", control:CONTROL_FORCE}, ijkFormat);
var aOutput = createOutputVariable({prefix:"A"}, abcFormat);
var bOutput = createOutputVariable({prefix:"B"}, abcFormat);
var cOutput = createOutputVariable({prefix:"C"}, abcFormat);
var feedOutput = createOutputVariable({prefix:"F"}, feedFormat);
var inverseTimeOutput = createOutputVariable({prefix:"F", control:CONTROL_FORCE}, inverseTimeFormat);
var pitchOutput = createOutputVariable({prefix:"F", control:CONTROL_FORCE}, pitchFormat);
var sOutput = createOutputVariable({prefix:"S", control:CONTROL_FORCE}, rpmFormat);
var peckOutput = createOutputVariable({prefix:"Q", control:CONTROL_FORCE}, peckFormat);

// circular output
var iOutput = createOutputVariable({prefix:"I", control:CONTROL_NONZERO}, xyzFormat);
var jOutput = createOutputVariable({prefix:"J", control:CONTROL_NONZERO}, xyzFormat);
var kOutput = createOutputVariable({prefix:"K", control:CONTROL_NONZERO}, xyzFormat);

var gMotionModal = createOutputVariable({onchange:function() {if (skipBlocks) {forceModals(gMotionModal);}}}, gFormat); // modal group 1 // G0-G3, ...
var gPlaneModal = createOutputVariable({onchange:function() {if (skipBlocks) {forceModals(gPlaneModal);} forceModals(gMotionModal);}}, gFormat); // modal group 2 // G17-19
var gAbsIncModal = createOutputVariable({onchange:function() {if (skipBlocks) {forceModals(gAbsIncModal);}}}, gFormat); // modal group 3 // G90-91
var gFeedModeModal = createOutputVariable({}, gFormat); // modal group 5 // G94-95
var gUnitModal = createOutputVariable({}, gFormat); // modal group 6 // G20-21
var gCycleModal = createOutputVariable({}, gFormat); // modal group 9 // G81, ...
var gRetractModal = createOutputVariable({}, gFormat); // modal group 10 // G98-99
var rotaryAxisClamp = createOutputVariable({}, mFormat);

var settings = {
  maximumToolNumber: 9999, // Matsuura tool-management T-NO range is 1-9999; do not limit tool numbers by magazine pocket count.
  coolant: {
    // samples:
    // {id: COOLANT_THROUGH_TOOL, on: 88, off: 89}
    // {id: COOLANT_THROUGH_TOOL, on: [8, 88], off: [9, 89]}
    // {id: COOLANT_THROUGH_TOOL, on: "M88 P3 (myComment)", off: "M89"}
    coolants: [
      {id:COOLANT_FLOOD, on:8},
      {id:COOLANT_MIST},
      {id:COOLANT_THROUGH_TOOL, on:88, off:89},
      {id:COOLANT_AIR},
      {id:COOLANT_AIR_THROUGH_TOOL},
      {id:COOLANT_SUCTION},
      {id:COOLANT_FLOOD_MIST},
      {id:COOLANT_FLOOD_THROUGH_TOOL, on:[8, 88], off:[9, 89]},
      {id:COOLANT_OFF, off:9}
    ],
    singleLineCoolant: false, // specifies to output multiple coolant codes in one line rather than in separate lines
  },
  smoothing: {
    roughing              : 1, // roughing level for smoothing in automatic mode
    semi                  : 2, // semi-roughing level for smoothing in automatic mode
    semifinishing         : 2, // semi-finishing level for smoothing in automatic mode
    finishing             : 3, // finishing level for smoothing in automatic mode
    thresholdRoughing     : toPreciseUnit(0.1, MM), // operations with stock/tolerance above that threshold will use roughing level in automatic mode
    thresholdFinishing    : toPreciseUnit(0.005, MM), // operations with stock/tolerance below that threshold will use finishing level in automatic mode
    thresholdSemiFinishing: toPreciseUnit(0.01, MM), // operations with stock/tolerance above finishing and below threshold roughing that threshold will use semi finishing level in automatic mode

    differenceCriteria: "level", // options: "level", "tolerance", "both". Specifies criteria when output smoothing codes
    autoLevelCriteria : "stock", // use "stock" or "tolerance" to determine levels in automatic mode
    cancelCompensation: true // tool length compensation must be canceled prior to changing the smoothing level
  },
  retract: {
    cancelRotationOnRetracting: false, // specifies that rotations (G68) need to be canceled prior to retracting
    methodXY                  : undefined, // special condition, overwrite retract behavior per axis
    methodZ                   : undefined, // special condition, overwrite retract behavior per axis
    useZeroValues             : ["G28", "G30"], // enter property value id(s) for using "0" value instead of machineConfiguration axes home position values (ie G30 Z0)
    homeXY                    : {onIndexing:false, onToolChange:false, onProgramEnd:{axes:[X, Y]}} // Specifies when the machine should be homed in X/Y. Sample: onIndexing:{axes:[X, Y], singleLine:false}
  },
  parametricFeeds: {
    firstFeedParameter    : 500, // specifies the initial parameter number to be used for parametric feedrate output
    feedAssignmentVariable: "#", // specifies the syntax to define a parameter
    feedOutputVariable    : "F#" // specifies the syntax to output the feedrate as parameter
  },
  machineAngles: { // refer to https://cam.autodesk.com/posts/reference/classMachineConfiguration.html#a14bcc7550639c482492b4ad05b1580c8
    controllingAxis: ABC,
    type           : PREFER_PREFERENCE,
    options        : ENABLE_ALL
  },
  workPlaneMethod: {
    useTiltedWorkplane    : true, // specifies that tilted workplanes should be used (ie. G68.2, G254, PLANE SPATIAL, CYCLE800), can be overwritten by property
    eulerConvention       : EULER_ZXZ_R, // specifies the euler convention (ie EULER_XYZ_R), set to undefined to use machine angles for TWP commands ('undefined' requires machine configuration)
    eulerCalculationMethod: "standard", // ('standard' / 'machine') 'machine' adjusts euler angles to match the machines ABC orientation, machine configuration required
    cancelTiltFirst       : true, // cancel tilted workplane prior to WCS (G54-G59) blocks
    forceMultiAxisIndexing: false, // force multi-axis indexing for 3D programs
    optimizeType          : OPTIMIZE_AXIS // can be set to OPTIMIZE_NONE, OPTIMIZE_BOTH, OPTIMIZE_TABLES, OPTIMIZE_HEADS, OPTIMIZE_AXIS. 'undefined' uses legacy rotations
  },
  subprograms: {
    initialSubprogramNumber: undefined, // specifies the initial number to be used for subprograms. 'undefined' uses the main program number
    minimumCyclePoints     : 5, // minimum number of points in cycle operation to consider for subprogram
    format                 : oFormat, // the format to use for the subprogam number format
    // objects below also accept strings with "%currentSubprogram" as placeholder. Sample: {files:["%"], embedded:"N" + "%currentSubprogram"}
    files                  : {extension:extension, prefix:undefined}, // specifies the subprogram file extension and the prefix to use for the generated file
    startBlock             : {files:["%" + EOL + "O"], embedded:["O"]}, // specifies the start syntax of a subprogram followed by the subprogram number
    endBlock               : {files:[mFormat.format(99) + EOL + "%"], embedded:[mFormat.format(99)]}, // specifies the command to for the end of a subprogram
    callBlock              : {files:[mFormat.format(98) + " P"], embedded:[mFormat.format(98) + " P"]} // specifies the command for calling a subprogram followed by the subprogram number
  },
  comments: {
    permittedCommentChars: " abcdefghijklmnopqrstuvwxyz0123456789.,=_-", // letters are not case sensitive, use option 'outputFormat' below. Set to 'undefined' to allow any character
    prefix               : "(", // specifies the prefix for the comment
    suffix               : ")", // specifies the suffix for the comment
    outputFormat         : "upperCase", // can be set to "upperCase", "lowerCase" and "ignoreCase". Set to "ignoreCase" to write comments without upper/lower case formatting
    maximumLineLength    : 80 // the maximum number of characters allowed in a line, set to 0 to disable comment output
  },
  probing: {
    probeAngleMethod       : undefined, // supported options are: OFF, AXIS_ROT, G68, G54.4. 'undefined' uses automatic selection
    probeAngleVariables    : {x:"#135", y:"#136", z:0, i:0, j:0, k:1, r:"#144", baseParamG54x4:26000, baseParamAxisRot:5200, method:0}, // specifies variables for the angle compensation macros, method 0 = Fanuc, 1 = Haas
    allowIndexingWCSProbing: false // specifies that probe WCS with tool orientation is supported
  },
  maximumSequenceNumber   : undefined, // the maximum sequence number (Nxxx), use 'undefined' for unlimited
  supportsToolVectorOutput: true, // specifies if the control does support tool axis vector output for multi axis toolpath
  polarCycleExpandMode    : 1 // 0=EXPAND_NONE: Does not expand any cycles. 1=EXPAND_TCP: Expands drilling cycles, when TCP is on. 2=EXPAND_NON_TCP: Expands drilling cycles, when TCP is off. 3=EXPAND_ALL: Expands all drilling cycles
};

var probeBaseNumber; // base number for probing macros

function onOpen() {
  // define and enable machine configuration
  receivedMachineConfiguration = machineConfiguration.isReceived();
  if (typeof defineMachine == "function") {
    defineMachine(); // hardcoded machine configuration
  }
  activateMachine(); // enable the machine optimizations and settings

  if (getProperty("useRadius")) {
    maximumCircularSweep = toRad(90); // avoid potential center calculation errors for CNC
  }

  if (!getProperty("separateWordsWithSpace")) {
    setWordSeparator("");
  }

  if (getProperty("forceIJK")) {
    iOutput.setControl(CONTROL_FORCE);
    jOutput.setControl(CONTROL_FORCE);
    kOutput.setControl(CONTROL_FORCE);
  }
  if (getProperty("useG95")) {
    if (getProperty("useParametricFeed")) {
      error(localize("Parametric feed is not supported when using G95."));
      return;
    }
    feedFormat.setNumberOfDecimals(unit == MM ? 4 : 5);
    feedOutput.setFormat(feedFormat);
  }
  probeBaseNumber = getProperty("probingMacros") == "matsuura" ? 0 : getProperty("probingMacros") == "renishaw" ? 9800 : 9500;
  matsuuraToolLengthSetTools = {};
  matsuuraToolBreakageCheckedTools = {};
  matsuuraPostCutRerunOperationIndex = 0;
  matsuuraHybridPostCutToolRunIndex = 0;
  clearMatsuuraPostCutRerunLabels();
  clearMatsuuraHybridPostCutToolRunState();
  clearMatsuuraPalletCfBodyState();
  matsuuraTailstockPending = false;
  matsuuraTailstockActive = false;
  matsuuraTailstockWasUsed = false;
  matsuuraTailstockDeferredPostCutTool = undefined;
  var mainProgramNumber = getProgramNumber();
  validateMatsuuraPalletOutputSettings(mainProgramNumber);
  validateMatsuuraFinalMultiTurnCReturnSettings();
  beginMatsuuraPalletCfBodyOutput(mainProgramNumber);

  writeln("%");
  var outputProgramNumber = useMatsuuraPalletCfBodyOutput() ? getMatsuuraPalletCfBodyProgram() : mainProgramNumber;
  var outputProgramFormat = useMatsuuraPalletCfBodyOutput() ? matsuuraPalletOFormat : oFormat;
  writeln("O" + outputProgramFormat.format(outputProgramNumber) + conditional(programComment, " " + formatComment(programComment)));
  if (matsuuraPalletCfBodyActive) {
    writeComment("PALLET CF WORK BODY - CALL FROM CNC MEMORY WITH M198 P" + matsuuraPalletOFormat.format(outputProgramNumber));
  }
  if (typeof inspectionWriteVariables == "function") {
    inspectionWriteVariables();
  }
  writeProgramHeader();

  if (getSetting("headPositioningMethod", 0) == 1 && machineConfiguration.isHeadConfiguration() && !is3D() && tcp.isSupportedByMachine && getSetting("workPlaneMethod.useTiltedWorkplane", false)) {
    for (var i = 0; i < getNumberOfSections(); ++i) {
      var section = getSection(i);
      if (!section.isMultiAxis() && defineWorkPlane(section, false).isNonZero()) {
        writeln("");
        var msg = "Ensure that the G49 command does not cause axis movement on your machine.";
        writeComment(msg);
        warning(localize(msg));
        onCommand(COMMAND_STOP);
        settings.allowCancelTCPBeforeRetracting = true;
        writeln("");
        break;
      }
    }
  }

  // absolute coordinates and feed per min
  writeBlock(gAbsIncModal.format(90), gFeedModeModal.format(getProperty("useG95") ? 95 : 94), gPlaneModal.format(17), toolLengthCompOutput.format(49), gFormat.format(40), gFormat.format(80));
  writeBlock(gUnitModal.format(unit == MM ? 21 : 20));
  validateCommonParameters();
  writeMatsuuraToolLengthAutomationAtProgramStart();
}

var previousPrefix;
function initializeSmoothingPrefix() {
  previousPrefix = smoothing.prefix;
  smoothing.prefix = "F"; // production baseline: keep G131 on proven F-level smoothing
  if (smoothing.prefix != previousPrefix) {
    smoothing.level = Number.POSITIVE_INFINITY; // reset smoothing level to force 'isDifferent' parameter
    smoothing.tolerance = Number.POSITIVE_INFINITY; // reset smoothing tolerance to force 'isDifferent' parameter
  }
}

function isMatsuuraToolLengthAutomationEnabled() {
  return getProperty("matsuuraToolLengthSetMode") != "off" ||
    getProperty("matsuuraToolBreakageCheckMode") != "off" ||
    getProperty("matsuuraToolBreakagePostCutMode") != "off";
}

function isMatsuuraToolLengthAutomationTool(tool) {
  return tool && tool.type != TOOL_PROBE;
}

function getMatsuuraToolOffsetSource() {
  var source = getProperty("matsuuraToolOffsetSource", "fusionFixed");
  if (source != "fusionFixed" && source != "matsuuraSelectedPotVariables") {
    error("Unsupported Tool offset source: " + source + ".");
  }
  return source;
}

function useMatsuuraToolManagementOffsetVariables() {
  return getMatsuuraToolOffsetSource() == "matsuuraSelectedPotVariables";
}

function getMatsuuraToolLengthOffsetWord(tool) {
  if (!getSetting("outputToolLengthOffset", true)) {
    return "";
  }
  if (useMatsuuraToolManagementOffsetVariables() && isMatsuuraToolLengthAutomationTool(tool)) {
    return "H#518";
  }
  return hFormat.format(tool.lengthOffset);
}

function getMatsuuraToolDiameterOffsetWord(tool) {
  if (!getSetting("outputToolDiameterOffset", true)) {
    return "";
  }
  if (useMatsuuraToolManagementOffsetVariables() && isMatsuuraToolLengthAutomationTool(tool)) {
    return "D#517";
  }
  return diameterOffsetFormat.format(tool.diameterOffset);
}

function getMatsuuraToolLengthAutomationKey(tool) {
  return Math.round(tool.number) + ":" + Math.round(tool.lengthOffset);
}

function validateMatsuuraToolLengthAutomationTool(tool) {
  if (!isMatsuuraToolLengthAutomationTool(tool)) {
    return;
  }
  if (tool.number < 1 || Math.abs(tool.number - Math.round(tool.number)) > 1e-9) {
    error("Tool length automation requires a positive integer T number. Check tool " + tool.number + ".");
  }
  if (tool.lengthOffset < 1 || Math.abs(tool.lengthOffset - Math.round(tool.lengthOffset)) > 1e-9) {
    error("Tool length automation requires a positive integer H offset. Check T" + toolFormat.format(tool.number) + ".");
  }
}

function getMatsuuraToolLengthSetCycle() {
  var cycle = getProperty("matsuuraToolLengthSetCycle", "normalO9303");
  if (cycle != "normalO9303" && cycle != "fastRoughHO1938") {
    error("Unsupported Tool length set cycle: " + cycle + ".");
  }
  return cycle;
}

function getMatsuuraToolBreakagePostCutMode() {
  var mode = getProperty("matsuuraToolBreakagePostCutMode", "off");
  if (mode != "off" && mode != "afterToolRun" && mode != "afterEachOperation") {
    error("Unsupported Post-cut tool breakage check mode: " + mode + ".");
  }
  return mode;
}

function getMatsuuraPostCutRerunOutputMode() {
  var mode = getProperty("matsuuraPostCutRerunOutputMode", "memorySingle");
  if (mode != "memorySingle" && mode != "hybridMemoryCf") {
    error("Unsupported Post-cut sister rerun output: " + mode + ".");
  }
  return mode;
}

function getMatsuuraToolBreakageAction() {
  var action = getProperty("matsuuraToolBreakageAction", "alarmStop");
  if (action != "alarmStop" && action != "trySisterTool") {
    error("Unsupported Broken tool action: " + action + ".");
  }
  return action;
}

function useMatsuuraSisterToolRecovery() {
  return getMatsuuraToolBreakageAction() == "trySisterTool";
}

function useMatsuuraPostCutRerunRecovery() {
  return useMatsuuraSisterToolRecovery() && getMatsuuraToolBreakagePostCutMode() != "off";
}

function useMatsuuraHybridPostCutRerun() {
  return useMatsuuraPostCutRerunRecovery() && getMatsuuraPostCutRerunOutputMode() == "hybridMemoryCf";
}

function shouldWriteMatsuuraPostCutRerunGuard(tool) {
  return useMatsuuraPostCutRerunRecovery() && isMatsuuraToolLengthAutomationTool(tool);
}

function getMatsuuraHybridToolRunFirstProgram() {
  var programNumber = parseInt(getProperty("matsuuraHybridToolRunFirstProgram", 3001), 10);
  if (!isFinite(programNumber) || programNumber < 1 || programNumber > 9999) {
    error("CF tool-run first O-number must be between 1 and 9999.");
  }
  return programNumber;
}

function getMatsuuraHybridPostCutToolRunCount() {
  var count = 0;
  var previousKey = "";
  for (var i = 0; i < getNumberOfSections(); ++i) {
    var sectionTool = getSection(i).getTool();
    if (!isMatsuuraToolLengthAutomationTool(sectionTool)) {
      previousKey = "";
      continue;
    }
    var key = getMatsuuraToolLengthAutomationKey(sectionTool);
    if (key != previousKey) {
      ++count;
      previousKey = key;
    }
  }
  return count;
}

function validateMatsuuraHybridPostCutRerunSettings() {
  if (!useMatsuuraHybridPostCutRerun()) {
    return;
  }
  if (getMatsuuraToolBreakagePostCutMode() != "afterToolRun") {
    error("Hybrid post-cut sister rerun supports only Post-cut tool breakage check mode = After each tool run.");
  }
  if (getProperty("useSubroutines", "none") != "none") {
    error("Hybrid post-cut sister rerun requires 'Use subroutines' = No.");
  }
  if (getProperty("useFilesForSubprograms", false)) {
    error("Hybrid post-cut sister rerun requires 'Use files for subroutines' = No.");
  }
  if (getProperty("useLiveConnection", false)) {
    error("Hybrid post-cut sister rerun does not allow inspection live connection because the scheduler main uses IF/GOTO.");
  }
  if (isMatsuuraApcEndExchangeEnabled()) {
    error("Hybrid post-cut sister rerun cannot be combined with End-of-job APC exchange.");
  }

  var firstProgram = getMatsuuraHybridToolRunFirstProgram();
  var toolRunCount = getMatsuuraHybridPostCutToolRunCount();
  if (toolRunCount < 1) {
    return;
  }
  var lastProgram = firstProgram + toolRunCount - 1;
  if (lastProgram > 9999) {
    error("Hybrid post-cut sister rerun needs " + toolRunCount + " CF tool-run programs. Reduce CF tool-run first O-number so the last file is not above O9999.");
  }
  var reservedPrograms = [1938, 1939, 1940, 9001, 9301, 9303, 9999, getProgramNumber()];
  for (var programNumber = firstProgram; programNumber <= lastProgram; ++programNumber) {
    if (programNumber >= 8000 && programNumber <= 9999) {
      error("Hybrid CF tool-run O" + oFormat.format(programNumber) + " is in the reserved 8000-9999 range. Choose a lower CF tool-run first O-number.");
    }
    if (reservedPrograms.indexOf(programNumber) != -1) {
      error("Hybrid CF tool-run O" + oFormat.format(programNumber) + " conflicts with the main program or a required macro number.");
    }
  }
  warning("Hybrid post-cut sister rerun writes a scheduler main for CNC memory and CF tool-run files O" + oFormat.format(firstProgram) + " through O" + oFormat.format(lastProgram) + " with no extension. Run the scheduler main from CNC memory, not directly from CF.");
}

function getMatsuuraToolLengthAutomationTools() {
  var keys = [];
  var tools = [];
  for (var i = 0; i < getNumberOfSections(); ++i) {
    var sectionTool = getSection(i).getTool();
    if (!isMatsuuraToolLengthAutomationTool(sectionTool)) {
      continue;
    }
    var key = getMatsuuraToolLengthAutomationKey(sectionTool);
    if (keys.indexOf(key) == -1) {
      keys.push(key);
      tools.push(sectionTool);
    }
  }
  return tools;
}

function validateMatsuuraToolLengthAutomationSettings() {
  if (!isMatsuuraToolLengthAutomationEnabled()) {
    return;
  }
  if (getProperty("matsuuraToolLengthSetMode") != "off" && getMatsuuraToolLengthSetCycle() == "fastRoughHO1938") {
    warning("Fast rough-H tool length setting outputs O1938 with Q10 D10 E200 F30 Z-5. Use only with trusted rough H values and O1938 loaded in CNC memory.");
  }
  if (getProperty("matsuuraToolBreakageCheckMode") != "off" || getMatsuuraToolBreakagePostCutMode() != "off") {
    getMatsuuraToolBreakageTolerance();
  }
  if (useMatsuuraSisterToolRecovery()) {
    if (!useMatsuuraToolManagementOffsetVariables()) {
      error("Broken tool action = Try sister tool requires Tool offset source = Matsuura selected pot #518/#517.");
    }
    if (getProperty("matsuuraToolBreakageCheckMode") == "off" && getMatsuuraToolBreakagePostCutMode() == "off") {
      error("Broken tool action = Try sister tool requires either a pre-cut Tool breakage check mode or a Post-cut tool breakage check mode.");
    }
    if (getProperty("matsuuraToolBreakageCheckMode") == "allAtProgramStart") {
      error("Broken tool action = Try sister tool requires breakage checks after M6. Do not use Tool breakage check mode = All tools at program start.");
    }
    if (useMatsuuraHybridPostCutRerun()) {
      warning("Broken tool action = Try sister tool requires O1939/O9999 loaded for pre-cut recovery. Hybrid post-cut rerun also requires O1940 loaded in CNC memory and no-cut proof before production.");
    } else {
      warning("Broken tool action = Try sister tool requires O1939/O9999 loaded for pre-cut recovery. Post-cut rerun recovery also requires O1940, main-program IF/GOTO support, and no-cut proof before production. For production-style post-cut recovery, use Post-cut tool breakage check mode = After each tool run.");
    }
  }
  validateMatsuuraHybridPostCutRerunSettings();
  var tools = getMatsuuraToolLengthAutomationTools();
  for (var i = 0; i < tools.length; ++i) {
    validateMatsuuraToolLengthAutomationTool(tools[i]);
  }
}

function validateMatsuuraToolManagementOffsetSettings() {
  if (!useMatsuuraToolManagementOffsetVariables()) {
    return;
  }
  warning("Tool offset source = Matsuura selected pot #518/#517 is experimental. Use only after Tool Manage duplicate T-NO/SEL and #517/#518 proof on the machine.");
  if (getProperty("matsuuraToolLengthSetMode") == "allAtProgramStart") {
    error("Tool offset source = Matsuura selected pot #518/#517 requires a selected tool after M6. Do not use Tool length set mode = All tools at program start.");
  }
  if (getProperty("matsuuraToolLengthSetMode") != "off") {
    warning("Tool length set mode with selected-pot #518 uses H#518 after M6. Proof this combination carefully before production use.");
  }
  if (getProperty("matsuuraToolBreakageCheckMode") == "allAtProgramStart") {
    error("Tool offset source = Matsuura selected pot #518/#517 requires breakage checks after M6. Do not use Tool breakage check mode = All tools at program start.");
  }
}

function validateMatsuuraCfCardSafeOutputSettings() {
  if (!getProperty("matsuuraCfCardSafeOutput")) {
    return;
  }
  if (getProperty("useSubroutines", "none") != "none") {
    error("CF card safe output requires 'Use subroutines' = No. CF-card jobs on this machine should not rely on main-program M98/M99 subroutine calls.");
  }
  if (getProperty("useFilesForSubprograms", false)) {
    error("CF card safe output requires 'Use files for subroutines' = No.");
  }
  if (getProperty("useLiveConnection", false)) {
    error("CF card safe output does not allow inspection live connection because it can output main-program IF/GOTO blocks.");
  }
  if (useMatsuuraPostCutRerunRecovery() && !useMatsuuraHybridPostCutRerun()) {
    error("CF card safe output cannot be used with post-cut sister-tool rerun recovery because that mode outputs main-program IF/GOTO control flow.");
  }
}

function getMatsuuraPalletOutputMode() {
  var mode = getProperty("matsuuraPalletOutputMode", "off");
  if (mode != "off" && mode != "cfBody" && mode != "dataServerSchedule") {
    error("Unsupported Pallet / APC output mode: " + mode + ".");
  }
  return mode;
}

function useMatsuuraPalletCfBodyOutput() {
  return getMatsuuraPalletOutputMode() == "cfBody";
}

function useMatsuuraPalletDataServerScheduleOutput() {
  return getMatsuuraPalletOutputMode() == "dataServerSchedule";
}

function getMatsuuraPalletCfBodyProgram() {
  var programNumber = parseInt(getProperty("matsuuraPalletCfBodyProgram", 3601), 10);
  if (!isFinite(programNumber) || programNumber < 1 || programNumber > 9999) {
    error("Pallet CF body O-number must be between 1 and 9999.");
  }
  return programNumber;
}

function getMatsuuraPalletLoaderFinishMode() {
  var mode = getProperty("matsuuraPalletLoaderFinish", "singleM30");
  if (mode != "singleM30" && mode != "scheduleReturn") {
    error("Unsupported Pallet memory loader finish: " + mode + ".");
  }
  return mode;
}

function getMatsuuraPalletStartProgram(reportOverride) {
  var configuredProgram = parseInt(getProperty("matsuuraPalletStartProgram", 1), 10);
  if (reportOverride && configuredProgram != 1) {
    warning("Configured Shared Pallet Start Program O" + (isFinite(configuredProgram) ? oFormat.format(configuredProgram) : "????") + " is ignored. Schedule output is forced to recorded O0001.");
  }
  return 1;
}

function getMatsuuraPalletDataServerStartProgram() {
  return 6597;
}

function getMatsuuraPalletCfBodyFilePath(programNumber) {
  return FileSystem.getCombinedPath(FileSystem.getFolderPath(getOutputPath()), "O" + matsuuraPalletOFormat.format(programNumber));
}

function clearMatsuuraPalletCfBodyState() {
  matsuuraPalletCfBodyActive = false;
  matsuuraPalletCfApcInspectionAway = false;
  matsuuraPalletCfApcActionWriting = false;
}

function validateMatsuuraPalletCfApcInspectionClosed() {
  if (!matsuuraPalletCfApcInspectionAway) {
    return true;
  }
  error("Pallet CF work body cannot end while its original pallet is away for inspection. Add the matching APC_EXCHANGE return Action before machining or M99.");
  return false;
}

function validateMatsuuraPalletMemoryLoaderSettings(mainProgramNumber) {
  if (!useMatsuuraPalletCfBodyOutput()) {
    return;
  }

  var bodyProgram = getMatsuuraPalletCfBodyProgram();
  if (mainProgramNumber != bodyProgram) {
    var mismatchMessage = "Pallet package NC Program number O" + oFormat.format(mainProgramNumber) + " must match Pallet CF body O-number O" + matsuuraPalletOFormat.format(bodyProgram) + ".";
    if (getSimulationStreamPath() != "") {
      warning("SIMULATION ONLY: " + mismatchMessage + " Actual NC posting remains blocked until the numbers match.");
    } else {
      error(mismatchMessage);
    }
  }

  if (getMatsuuraPalletLoaderFinishMode() == "scheduleReturn") {
    var startProgram = getMatsuuraPalletStartProgram(true);
    if (mainProgramNumber == startProgram) {
      error("Pallet memory loader O" + oFormat.format(mainProgramNumber) + " cannot equal Pallet Start Program O" + oFormat.format(startProgram) + ".");
    }
    warning("SCHEDULE PROOF: memory loader O" + oFormat.format(mainProgramNumber) + " returns to Start Program O" + oFormat.format(startProgram) + " with M98. Verify the Start Program, End [O], Schedule order, and first-current-pallet launch path without cutting.");
  }
}

function validateMatsuuraPalletDataServerScheduleSettings(mainProgramNumber) {
  if (!useMatsuuraPalletDataServerScheduleOutput()) {
    return;
  }

  var startProgram = getMatsuuraPalletDataServerStartProgram();
  if (mainProgramNumber == startProgram) {
    error("Direct DATA_SV work program O" + oFormat.format(mainProgramNumber) + " cannot equal CNC-memory Start Program O" + oFormat.format(startProgram) + ".");
  }
  if (useMatsuuraPostCutRerunRecovery()) {
    error("Direct DATA_SV schedule output cannot be combined with post-cut sister-tool rerun recovery. That workflow creates separate rerun files and is not a one-file pallet program.");
  }
  if (getProperty("useSubroutines", "none") != "none") {
    error("Direct DATA_SV schedule requires 'Use subroutines' = No until Data Server main/subprogram lookup is separately proven.");
  }
  if (getProperty("useFilesForSubprograms", false)) {
    error("Direct DATA_SV schedule requires 'Use files for subroutines' = No. The guarded path must remain one complete work-program file.");
  }
  if (getProperty("useLiveConnection", false)) {
    error("Direct DATA_SV schedule does not allow inspection live connection until its main-program control flow is separately proven.");
  }
  if (isMatsuuraApcEndExchangeEnabled()) {
    error("Direct DATA_SV schedule output cannot be combined with End-of-job APC exchange. The work program must return with M98 P6597 so CNC-memory O6597 owns the scheduled exchange.");
  }
  warning("MACHINE-PASSED NO-CUT: Direct DATA_SV schedule writes one complete work program and returns to CNC-memory O" + oFormat.format(startProgram) + " with M98. It does not write a CNC-memory loader, M198 call, CF body, M99, or final M30. Pallet Manager Start Program must be O6597 and SPECIAL must be CON. Run the first production cutting proof controlled and attended.");
}

function validateMatsuuraPalletOutputSettings(mainProgramNumber) {
  if (useMatsuuraPalletDataServerScheduleOutput()) {
    validateMatsuuraPalletDataServerScheduleSettings(mainProgramNumber);
    return;
  }
  if (!useMatsuuraPalletCfBodyOutput()) {
    return;
  }
  if (!getProperty("matsuuraCfCardSafeOutput")) {
    error("Pallet CF work body requires 'CF card safe output' = Yes.");
  }
  validateMatsuuraCfCardSafeOutputSettings();
  if (useMatsuuraPostCutRerunRecovery()) {
    error("Pallet CF work body cannot be combined with post-cut sister-tool rerun recovery. Use the separate Hybrid post-cut output for that workflow.");
  }
  if (isMatsuuraApcEndExchangeEnabled()) {
    error("Pallet CF work body cannot be combined with End-of-job APC exchange. Pallet selection and exchange belong in the separate CNC-memory pallet program.");
  }
  if (getProperty("matsuuraPalletCfApcInspectionProof", false)) {
    warning("PROOF ONLY: APC_EXCHANGE inside a Pallet CF work body must be a matched inspection OUT/RETURN pair. Only M00/M01 may occur while the loader's original pallet is away. Verify every M61, Ready/NEXT state, and the final M99 return in Single Block before production use.");
  }

  var programNumber = getMatsuuraPalletCfBodyProgram();
  if (programNumber >= 8000 && programNumber <= 9999) {
    error("Pallet CF body O" + matsuuraPalletOFormat.format(programNumber) + " is in the reserved 8000-9999 range. Choose a lower O-number.");
  }
  var reservedPrograms = [1938, 1939, 1940, 9001, 9301, 9303, 9999];
  if (reservedPrograms.indexOf(programNumber) != -1) {
    error("Pallet CF body O" + matsuuraPalletOFormat.format(programNumber) + " conflicts with a required Matsuura macro number.");
  }
  validateMatsuuraPalletMemoryLoaderSettings(mainProgramNumber);
  warning("Pallet package writes the selected .nc output as CNC-memory loader O" + oFormat.format(mainProgramNumber) + " and writes external O" + matsuuraPalletOFormat.format(programNumber) + " with no extension. Load the .nc file into CNC memory and put the no-extension O file on CF/REMOTE.");
}

function writeMatsuuraPalletMemoryLoader(mainProgramNumber) {
  if (!useMatsuuraPalletCfBodyOutput()) {
    return;
  }

  var bodyProgram = getMatsuuraPalletCfBodyProgram();
  writeln("%");
  writeln("O" + oFormat.format(mainProgramNumber));
  writeComment("PALLET MEMORY LOADER - RUN FROM CNC MEMORY ONLY");
  writeComment("CALL CF REMOTE BODY O" + matsuuraPalletOFormat.format(bodyProgram));
  writeBlock(mFormat.format(198), "P" + matsuuraPalletOFormat.format(bodyProgram));
  if (getMatsuuraPalletLoaderFinishMode() == "scheduleReturn") {
    writeBlock(mFormat.format(98), "P" + oFormat.format(getMatsuuraPalletStartProgram()));
  } else {
    writeBlock(mFormat.format(30));
  }
  writeln("%");
}

function writeMatsuuraPalletProgramEnd() {
  if (useMatsuuraPalletDataServerScheduleOutput()) {
    writeBlock(mFormat.format(98), "P" + oFormat.format(getMatsuuraPalletDataServerStartProgram()));
    return;
  }
  writeBlock(mFormat.format(30));
}

function beginMatsuuraPalletCfBodyOutput(mainProgramNumber) {
  if (!useMatsuuraPalletCfBodyOutput()) {
    return;
  }
  writeMatsuuraPalletMemoryLoader(mainProgramNumber);
  sequenceNumber = undefined;
  redirectToFile(getMatsuuraPalletCfBodyFilePath(getMatsuuraPalletCfBodyProgram()));
  matsuuraPalletCfBodyActive = true;
}

function isMatsuuraApcEndExchangeEnabled() {
  return getProperty("matsuuraApcEndExchange", false);
}

var matsuuraPhysicalRotaryReferenceReturned = false;

function validateMatsuuraFinalMultiTurnCReturnSettings() {
  if (!getProperty("matsuuraFinalMultiTurnCReturn", false)) {
    return;
  }
  if (useMatsuuraPalletCfBodyOutput()) {
    error("Multi-turn C reference return cannot be combined with Pallet CF work-body output until that M99 return path is separately proven.");
    return;
  }
  if (isMatsuuraApcEndExchangeEnabled()) {
    warning("PROOF ONLY: Multi-turn C reference return with End-of-job APC exchange keeps guarded B/C reference returns at supported neutral-entry and closeout seams before the field-passed APC tail. Verify every generated reference-return seam and run a no-cut machine proof before production use.");
    return;
  }
  warning("PROOF ONLY: Multi-turn C reference return changes B/C motion at guarded neutral TCP entries, TCP-to-indexed section entries, and final closeout when |C| is greater than 360 degrees. Verify every generated reference-return seam and run a no-cut machine proof before production use.");
}

function shouldUseMatsuuraMultiTurnCReferenceReturn(_currentABC) {
  if (!getProperty("matsuuraFinalMultiTurnCReturn", false) ||
      useMatsuuraPalletCfBodyOutput() || matsuuraPalletCfBodyActive ||
      matsuuraTailstockPending || matsuuraTailstockActive || matsuuraTailstockWasUsed || !machineConfiguration.isMultiAxisConfiguration()) {
    return false;
  }
  var currentABC = _currentABC || getCurrentDirection();
  return currentABC && isFinite(currentABC.z) && (Math.abs(currentABC.z) > (toRad(360) + 1e-6));
}

function shouldUseMatsuuraFinalMultiTurnCReturn() {
  return shouldUseMatsuuraMultiTurnCReferenceReturn();
}

function writeMatsuuraPhysicalRotaryReferenceReturn() {
  var zeroABC = new Vector(0, 0, 0);
  onCommand(COMMAND_UNLOCK_MULTI_AXIS);
  forceModals(gAbsIncModal, gMotionModal);
  writeBlock(gFormat.format(28), gAbsIncModal.format(91), "B" + abcFormat.format(0), "C" + abcFormat.format(0));
  writeBlock(gAbsIncModal.format(90));
  gMotionModal.reset();
  setCurrentABC(zeroABC);
  currentWorkPlaneABC = zeroABC;
  bOutput.reset();
  cOutput.reset();
  matsuuraPhysicalRotaryReferenceReturned = true;
  machineSimulation({a:0, b:0, c:0, coordinates:MACHINE});
}

function writeMatsuuraNeutralRotaryEntry(matsuuraPreviousABC, seamDescription) {
  var zeroABC = new Vector(0, 0, 0);
  if (!shouldUseMatsuuraMultiTurnCReferenceReturn(matsuuraPreviousABC)) {
    if (matsuuraPhysicalRotaryReferenceReturned && matsuuraPreviousABC &&
        Math.abs(matsuuraPreviousABC.x) <= 1e-6 &&
        Math.abs(matsuuraPreviousABC.y) <= 1e-6 &&
        Math.abs(matsuuraPreviousABC.z) <= 1e-6) {
      // A physical G28 B/C reference return already established this neutral pose.
      // Do not emit another absolute B0/C0 after later tool/section modal resets.
      return;
    }
    matsuuraPhysicalRotaryReferenceReturned = false;
    positionABC(zeroABC);
    return;
  }
  if (!state.retractedZ || state.lengthCompensationActive || state.tcpIsActive || state.twpIsActive || matsuuraOutputTwpIsActive) {
    error("Multi-turn C reference return requires Z at machine home with G49, G69, and TCP inactive before the " + seamDescription + ".");
    return;
  }

  var restoreSmoothing = smoothing.isActive;
  if (restoreSmoothing) {
    setSmoothing(false);
  }
  writeMatsuuraPhysicalRotaryReferenceReturn();
  if (restoreSmoothing) {
    setSmoothing(true);
  }
}

function writeMatsuuraTCPNeutralRotaryEntry(matsuuraPreviousABC) {
  writeMatsuuraNeutralRotaryEntry(matsuuraPreviousABC, "neutral TCP entry");
}

function writeMatsuuraIndexedNeutralRotaryEntry(matsuuraPreviousABC) {
  writeMatsuuraNeutralRotaryEntry(matsuuraPreviousABC, "neutral indexed-section entry");
}

function writeMatsuuraFinalRotaryCloseout() {
  if (!shouldUseMatsuuraFinalMultiTurnCReturn()) {
    setWorkPlane(new Vector(0, 0, 0));
    return;
  }

  writeMatsuuraPhysicalRotaryReferenceReturn();
  if (!currentSection.isMultiAxis()) {
    onCommand(COMMAND_LOCK_MULTI_AXIS);
  }
}

function validateMatsuuraApcEndExchangeSettings() {
  if (!isMatsuuraApcEndExchangeEnabled()) {
    return;
  }
  if (!getProperty("matsuuraCfCardSafeOutput")) {
    error("End-of-job APC exchange requires 'CF card safe output' = Yes.");
  }
}

function writeMatsuuraApcEndExchange() {
  if (!isMatsuuraApcEndExchangeEnabled()) {
    return;
  }

  writeln("");
  writeComment("APC END EXCHANGE");
  forceModals(gAbsIncModal, gPlaneModal);
  writeBlock(gAbsIncModal.format(90), gPlaneModal.format(17), gFormat.format(40), toolLengthCompOutput.format(49), gFormat.format(80));
  writeBlock(gFormat.format(69));
  writeBlock(gFormat.format(130));
  writeBlock(mFormat.format(16));
  writeBlock(mFormat.format(9));
  forceModals(gAbsIncModal);
  writeBlock(gAbsIncModal.format(91), gFormat.format(28), "Z" + xyzFormat.format(0));
  writeBlock(gFormat.format(30), "X" + xyzFormat.format(0), "P2");
  writeBlock(mFormat.format(22));
  writeBlock(mFormat.format(24));
  forceModals(gAbsIncModal);
  writeBlock(gFormat.format(28), gAbsIncModal.format(91), "Y" + xyzFormat.format(0), "B" + abcFormat.format(0), "C" + abcFormat.format(0));
  writeBlock(mFormat.format(21));
  writeBlock(mFormat.format(23));
  writeBlock(mFormat.format(61));
}

function validateMatsuuraApcExchangeActionSettings() {
  if (!getProperty("matsuuraCfCardSafeOutput")) {
    error("APC_EXCHANGE requires 'CF card safe output' = Yes.");
    return false;
  }
  if (useMatsuuraPalletDataServerScheduleOutput()) {
    error("APC_EXCHANGE cannot be combined with Direct DATA_SV schedule output. CNC-memory O6597 must own pallet exchange for this path.");
    return false;
  }
  if (matsuuraTailstockPending || matsuuraTailstockActive || matsuuraTailstockWasUsed) {
    error("APC_EXCHANGE cannot be combined with tailstock Actions until that workflow is separately proven.");
    return false;
  }
  var palletCfBody = useMatsuuraPalletCfBodyOutput() || matsuuraPalletCfBodyActive;
  if (palletCfBody && !getProperty("matsuuraPalletCfApcInspectionProof", false)) {
    error("APC_EXCHANGE inside a Pallet CF work-body program requires 'CF-body APC inspection pair (proof)' = Yes.");
    return false;
  }
  if (useMatsuuraPostCutRerunRecovery()) {
    error("APC_EXCHANGE cannot be combined with post-cut sister-tool rerun recovery until that control-flow path is separately proven.");
    return false;
  }
  if (useMatsuuraSisterToolRecovery()) {
    error("APC_EXCHANGE cannot be combined with sister-tool recovery until that mixed workflow is separately proven.");
    return false;
  }
  if (getProperty("matsuuraFinalMultiTurnCReturn", false)) {
    error("APC_EXCHANGE cannot be combined with Multi-turn C reference return until that rotary-state path is separately proven.");
    return false;
  }
  if (matsuuraProbeOnContinuesToNextSection) {
    error("APC_EXCHANGE cannot interrupt a continued probe-on sequence. Finish the probing sequence first.");
    return false;
  }
  var rotationCurrent = (typeof gRotationModal != "undefined") ? gRotationModal.getCurrent() : undefined;
  var twpIsActive = matsuuraOutputTwpIsActive || state.twpIsActive || ((rotationCurrent != undefined) && (rotationCurrent != 69));
  if (state.tcpIsActive || twpIsActive) {
    error("APC_EXCHANGE currently supports only a standard B0/C0 non-TCP section. Finish and cancel TCP/TWP before the Action.");
    return false;
  }
  var currentABC = getCurrentDirection();
  if (currentABC && (Math.abs(currentABC.x) > 1e-6 || Math.abs(currentABC.y) > 1e-6 || Math.abs(currentABC.z) > 1e-6)) {
    error("APC_EXCHANGE currently requires the post rotary state at B0/C0. Return to a standard B0/C0 section before the Action.");
    return false;
  }
  return true;
}

function writeMatsuuraApcExchangeAction() {
  if (!validateMatsuuraApcExchangeActionSettings()) {
    return;
  }

  var palletCfInspectionProof = (useMatsuuraPalletCfBodyOutput() || matsuuraPalletCfBodyActive) &&
    getProperty("matsuuraPalletCfApcInspectionProof", false);
  matsuuraPalletCfApcActionWriting = palletCfInspectionProof;
  writeln("");
  if (palletCfInspectionProof) {
    writeComment(matsuuraPalletCfApcInspectionAway ?
      "APC CF BODY INSPECTION RETURN - ORIGINAL PALLET REQUIRED" :
      "APC CF BODY INSPECTION OUT - ORIGINAL PALLET AWAY AFTER M61");
  } else {
    writeComment("APC SCHEDULED EXCHANGE - OPERATOR CONTROLS M00 M01");
  }
  onCommand(COMMAND_COOLANT_OFF);
  onCommand(COMMAND_STOP_SPINDLE);

  forceModals(gAbsIncModal, gMotionModal);
  writeBlock(gAbsIncModal.format(90), gFormat.format(53), gMotionModal.format(0), "Z" + xyzFormat.format(0));
  state.retractedZ = true;
  disableLengthCompensation(true);
  cancelWorkPlane(true);
  if (typeof smoothing != "undefined") {
    smoothing.force = true;
  }
  setSmoothing(false);

  forceModals(gAbsIncModal, gPlaneModal);
  writeBlock(gAbsIncModal.format(90), gPlaneModal.format(17), gFormat.format(40), gFormat.format(80));
  writeBlock(mFormat.format(16));
  writeBlock(mFormat.format(9));
  forceModals(gAbsIncModal);
  writeBlock(gAbsIncModal.format(91), gFormat.format(28), "Z" + xyzFormat.format(0));
  writeBlock(gFormat.format(30), "X" + xyzFormat.format(0), "P2");
  writeBlock(mFormat.format(22));
  writeBlock(mFormat.format(24));
  forceModals(gAbsIncModal);
  writeBlock(gFormat.format(28), gAbsIncModal.format(91), "Y" + xyzFormat.format(0), "B" + abcFormat.format(0), "C" + abcFormat.format(0));
  writeBlock(mFormat.format(21));
  writeBlock(mFormat.format(23));
  writeBlock(mFormat.format(61));
  forceModals(gAbsIncModal);
  writeBlock(gAbsIncModal.format(90));

  var zeroABC = new Vector(0, 0, 0);
  setCurrentABC(zeroABC);
  currentWorkPlaneABC = zeroABC;
  bOutput.reset();
  cOutput.reset();
  machineSimulation({a:0, b:0, c:0, coordinates:MACHINE});
  forceWorkPlane();
  currentWorkOffset = undefined;
  matsuuraOutputTwpIsActive = false;
  matsuuraOutputWorkOffset = undefined;
  matsuuraBClampedForLiveC = false;
  state.retractedX = true;
  state.retractedY = true;
  state.retractedZ = true;
  state.tcpIsActive = false;
  state.twpIsActive = false;
  state.lengthCompensationActive = false;
  forceSpindleSpeed = true;
  forceCoolant = true;
  forceModals();
  forceAny();
  if (palletCfInspectionProof) {
    matsuuraPalletCfApcInspectionAway = !matsuuraPalletCfApcInspectionAway;
    matsuuraPalletCfApcActionWriting = false;
  }
}

function formatMatsuuraToolLengthAutomationInteger(value) {
  return String(Math.round(value));
}

function formatMatsuuraToolLengthAutomationT(tool) {
  return "T" + formatMatsuuraToolLengthAutomationInteger(tool.number) + ".0";
}

function formatMatsuuraToolLengthAutomationH(tool) {
  if (useMatsuuraToolManagementOffsetVariables() && isMatsuuraToolLengthAutomationTool(tool)) {
    return "H#518";
  }
  return "H" + formatMatsuuraToolLengthAutomationInteger(tool.lengthOffset);
}

function formatMatsuuraToolBreakageH(tool) {
  if (useMatsuuraToolManagementOffsetVariables() && isMatsuuraToolLengthAutomationTool(tool)) {
    return "H#518";
  }
  return formatMatsuuraToolLengthAutomationH(tool);
}

function getMatsuuraToolBreakageTolerance() {
  var tolerance = parseFloat(getProperty("matsuuraToolBreakageTolerance", 0.5));
  if (!isFinite(tolerance) || tolerance <= 0) {
    error("Tool breakage tolerance D must be a positive number.");
  }
  return tolerance;
}

function formatMatsuuraToolBreakageToleranceD() {
  return "D" + xyzFormat.format(getMatsuuraToolBreakageTolerance());
}

function writeMatsuuraToolLengthAutomationSafeModal() {
  gAbsIncModal.reset();
  toolLengthCompOutput.reset();
  writeBlock(gAbsIncModal.format(90), gFormat.format(40), toolLengthCompOutput.format(49), gFormat.format(80));
  writeBlock(gFormat.format(54));
  currentWorkOffset = undefined; // force the real machining WCS after tool-setter macros use G54
}

function writeMatsuuraToolLengthSetCall(tool) {
  if (getMatsuuraToolLengthSetCycle() == "fastRoughHO1938") {
    writeComment("FAST TOOL LENGTH SET T" + formatMatsuuraToolLengthAutomationInteger(tool.number) + " H" + formatMatsuuraToolLengthAutomationInteger(tool.lengthOffset) + " ROUGH H");
    writeBlock(gFormat.format(65), "P1938", formatMatsuuraToolLengthAutomationT(tool), formatMatsuuraToolLengthAutomationH(tool), "Q10.", "D10.", "E200.", "F30.", "Z-5.");
    return;
  }
  writeComment("TOOL LENGTH SET T" + formatMatsuuraToolLengthAutomationInteger(tool.number) + " H" + formatMatsuuraToolLengthAutomationInteger(tool.lengthOffset));
  writeBlock(gFormat.format(65), "P9303", formatMatsuuraToolLengthAutomationT(tool), formatMatsuuraToolLengthAutomationH(tool), "M1.", "R-50.", "E200.", "Z-5.");
}

function writeMatsuuraToolBreakageCheckCall(tool, label, allowSisterRecovery, includeToolNumber) {
  var hWord = formatMatsuuraToolBreakageH(tool);
  if (useMatsuuraSisterToolRecovery() && allowSisterRecovery) {
    writeComment((label || "TOOL BREAKAGE CHECK") + " SISTER RECOVERY T" + formatMatsuuraToolLengthAutomationInteger(tool.number) + " " + hWord);
    writeBlock(gFormat.format(65), "P1939", formatMatsuuraToolLengthAutomationT(tool), hWord, formatMatsuuraToolBreakageToleranceD());
    writeMatsuuraToolLengthAutomationSafeModal();
    return;
  }
  writeComment((label || "TOOL BREAKAGE CHECK") + " T" + formatMatsuuraToolLengthAutomationInteger(tool.number) + " " + hWord);
  if (includeToolNumber === false) {
    writeBlock(gFormat.format(65), "P9301", hWord, formatMatsuuraToolBreakageToleranceD(), "M0.");
    writeMatsuuraToolLengthAutomationSafeModal();
    return;
  }
  writeBlock(gFormat.format(65), "P9301", formatMatsuuraToolLengthAutomationT(tool), hWord, formatMatsuuraToolBreakageToleranceD(), "M0.");
  writeMatsuuraToolLengthAutomationSafeModal();
}

function writeMatsuuraPostCutRerunRecoveryCheckCall(tool) {
  var hWord = formatMatsuuraToolBreakageH(tool);
  writeComment("POST-CUT TOOL BREAKAGE CHECK SISTER RERUN T" + formatMatsuuraToolLengthAutomationInteger(tool.number) + " " + hWord);
  writeBlock(gFormat.format(65), "P1940", formatMatsuuraToolLengthAutomationT(tool), hWord, formatMatsuuraToolBreakageToleranceD());
  writeMatsuuraToolLengthAutomationSafeModal();
}

function clearMatsuuraPostCutRerunLabels() {
  matsuuraPostCutRerunStartLabel = undefined;
  matsuuraPostCutRerunContinueLabel = undefined;
  matsuuraPostCutRerunAlarmLabel = undefined;
}

function clearMatsuuraHybridPostCutToolRunState() {
  matsuuraHybridPostCutToolRunActive = false;
  matsuuraHybridPostCutToolRunProgramNumber = undefined;
  matsuuraHybridPostCutToolRunFilePath = "";
}

function writeMatsuuraPostCutRerunLabel(label) {
  writeln("N" + label);
}

function isMatsuuraPostCutRerunToolRunStart(tool) {
  if (isFirstSection()) {
    return true;
  }
  var previousTool = getPreviousSection().getTool();
  if (!isMatsuuraToolLengthAutomationTool(previousTool)) {
    return true;
  }
  return getMatsuuraToolLengthAutomationKey(previousTool) != getMatsuuraToolLengthAutomationKey(tool);
}

function getMatsuuraHybridPostCutToolRunProgramNumber() {
  return getMatsuuraHybridToolRunFirstProgram() + matsuuraHybridPostCutToolRunIndex - 1;
}

function getMatsuuraHybridPostCutToolRunFilePath(programNumber) {
  return FileSystem.getCombinedPath(FileSystem.getFolderPath(getOutputPath()), "O" + oFormat.format(programNumber));
}

function writeMatsuuraHybridPostCutToolRunHeader(tool, programNumber) {
  writeln("%");
  writeln("O" + oFormat.format(programNumber) + " " + formatComment("CF TOOL RUN T" + formatMatsuuraToolLengthAutomationInteger(tool.number) + " FROM O" + oFormat.format(getProgramNumber())));
  writeComment("RUN FROM CNC-MEMORY SCHEDULER WITH M198 P" + oFormat.format(programNumber));
  gAbsIncModal.reset();
  gFeedModeModal.reset();
  gPlaneModal.reset();
  gUnitModal.reset();
  toolLengthCompOutput.reset();
  writeBlock(gAbsIncModal.format(90), gFeedModeModal.format(getProperty("useG95") ? 95 : 94), gPlaneModal.format(17), toolLengthCompOutput.format(49), gFormat.format(40), gFormat.format(80));
  writeBlock(gUnitModal.format(unit == MM ? 21 : 20));
  forceAny();
}

function writeMatsuuraHybridPostCutToolRunBegin(tool) {
  if (!shouldWriteMatsuuraPostCutRerunGuard(tool)) {
    return;
  }
  if (getMatsuuraToolBreakagePostCutMode() != "afterToolRun" || !isMatsuuraPostCutRerunToolRunStart(tool)) {
    return;
  }
  if (matsuuraHybridPostCutToolRunActive) {
    error("Hybrid post-cut sister rerun tried to start a new CF tool-run file before closing the previous one.");
  }

  clearMatsuuraPostCutRerunLabels();
  ++matsuuraPostCutRerunOperationIndex;
  var baseLabel = 5000 + (matsuuraPostCutRerunOperationIndex * 10);
  if (baseLabel + 3 > 9999) {
    error("Post-cut sister-tool rerun supports up to 499 guarded tool runs in one posted program.");
  }
  ++matsuuraHybridPostCutToolRunIndex;
  matsuuraHybridPostCutToolRunProgramNumber = getMatsuuraHybridPostCutToolRunProgramNumber();
  matsuuraHybridPostCutToolRunFilePath = getMatsuuraHybridPostCutToolRunFilePath(matsuuraHybridPostCutToolRunProgramNumber);
  matsuuraPostCutRerunStartLabel = baseLabel + 1;
  matsuuraPostCutRerunContinueLabel = baseLabel + 2;
  matsuuraPostCutRerunAlarmLabel = baseLabel + 3;

  writeln("");
  writeComment("HYBRID POST-CUT TOOL RUN RERUN GUARD T" + formatMatsuuraToolLengthAutomationInteger(tool.number) + " O" + oFormat.format(matsuuraHybridPostCutToolRunProgramNumber));
  writeBlock("#698=0");
  writeMatsuuraPostCutRerunLabel(matsuuraPostCutRerunStartLabel);
  writeBlock(mFormat.format(198), "P" + oFormat.format(matsuuraHybridPostCutToolRunProgramNumber));

  redirectToFile(matsuuraHybridPostCutToolRunFilePath);
  matsuuraHybridPostCutToolRunActive = true;
  writeMatsuuraHybridPostCutToolRunHeader(tool, matsuuraHybridPostCutToolRunProgramNumber);
}

function writeMatsuuraPostCutRerunBegin(tool) {
  if (useMatsuuraHybridPostCutRerun()) {
    writeMatsuuraHybridPostCutToolRunBegin(tool);
    return;
  }
  if (!shouldWriteMatsuuraPostCutRerunGuard(tool)) {
    return;
  }
  var postCutMode = getMatsuuraToolBreakagePostCutMode();
  if (postCutMode == "afterToolRun" && !isMatsuuraPostCutRerunToolRunStart(tool)) {
    return;
  }
  clearMatsuuraPostCutRerunLabels();
  ++matsuuraPostCutRerunOperationIndex;
  var baseLabel = 5000 + (matsuuraPostCutRerunOperationIndex * 10);
  if (baseLabel + 3 > 9999) {
    error("Post-cut sister-tool rerun supports up to 499 guarded tool runs/operations in one posted program.");
  }
  matsuuraPostCutRerunStartLabel = baseLabel + 1;
  matsuuraPostCutRerunContinueLabel = baseLabel + 2;
  matsuuraPostCutRerunAlarmLabel = baseLabel + 3;

  writeln("");
  writeComment((postCutMode == "afterToolRun" ? "POST-CUT TOOL RUN RERUN GUARD T" : "POST-CUT OPERATION RERUN GUARD T") + formatMatsuuraToolLengthAutomationInteger(tool.number));
  writeBlock("#698=0");
  writeMatsuuraPostCutRerunLabel(matsuuraPostCutRerunStartLabel);
}

function writeMatsuuraHybridPostCutToolRunEnd() {
  if (!useMatsuuraHybridPostCutRerun() || !matsuuraHybridPostCutToolRunActive) {
    return;
  }
  if (!shouldWriteMatsuuraPostCutToolBreakageCheck()) {
    return;
  }
  writeln("");
  writeComment("END CF TOOL RUN O" + oFormat.format(matsuuraHybridPostCutToolRunProgramNumber));
  writeBlock(mFormat.format(99));
  writeln("%");
  closeRedirection();
  clearMatsuuraHybridPostCutToolRunState();
  forceAny();
}

function writeMatsuuraPostCutRerunEnd() {
  if (matsuuraPostCutRerunStartLabel == undefined) {
    return;
  }
  writeBlock("IF[#699NE1]GOTO" + matsuuraPostCutRerunContinueLabel);
  writeBlock("#698=#698+1");
  writeBlock("IF[#698GT1]GOTO" + matsuuraPostCutRerunAlarmLabel);
  writeBlock("#699=0");
  writeBlock("GOTO" + matsuuraPostCutRerunStartLabel);
  writeMatsuuraPostCutRerunLabel(matsuuraPostCutRerunAlarmLabel);
  writeBlock("#3000=393(POSTCUT RERUN FAILED)");
  writeMatsuuraPostCutRerunLabel(matsuuraPostCutRerunContinueLabel);
  clearMatsuuraPostCutRerunLabels();
}

function shouldWriteMatsuuraPostCutToolBreakageCheck() {
  var mode = getMatsuuraToolBreakagePostCutMode();
  if (mode == "off" || !isMatsuuraToolLengthAutomationTool(tool)) {
    return false;
  }
  if (mode == "afterEachOperation") {
    return true;
  }
  if (isLastSection()) {
    return true;
  }
  var nextTool = getNextSection().getTool();
  if (!isMatsuuraToolLengthAutomationTool(nextTool)) {
    return true;
  }
  return getMatsuuraToolLengthAutomationKey(nextTool) != getMatsuuraToolLengthAutomationKey(tool);
}

function writeMatsuuraPostCutToolBreakageSafeModal() {
  gAbsIncModal.reset();
  toolLengthCompOutput.reset();
  writeBlock(gAbsIncModal.format(90), gFormat.format(40), toolLengthCompOutput.format(49), gFormat.format(80));
  cancelWorkPlane(true);
  setSmoothing(false);
  writeBlock(gFormat.format(54));
  currentWorkOffset = undefined; // force the real machining WCS after tool-setter macros use G54
}

function writeMatsuuraPostCutToolBreakageCheckForTool(checkTool) {
  validateMatsuuraToolLengthAutomationTool(checkTool);
  writeln("");
  onCommand(COMMAND_COOLANT_OFF);
  onCommand(COMMAND_STOP_SPINDLE);
  if (state.tcpIsActive) {
    disableLengthCompensation(true, true); // cancel TCP before any machine-coordinate retract
  }
  writeRetract(Z);
  writeMatsuuraPostCutToolBreakageSafeModal();
  if (useMatsuuraPostCutRerunRecovery()) {
    writeMatsuuraPostCutRerunRecoveryCheckCall(checkTool);
    writeMatsuuraPostCutRerunEnd();
  } else {
    writeMatsuuraToolBreakageCheckCall(checkTool, "POST-CUT TOOL BREAKAGE CHECK", false, false);
  }
  finalizeMatsuuraToolLengthAutomationOutput();
}

function writeMatsuuraPostCutToolBreakageCheck() {
  if (!shouldWriteMatsuuraPostCutToolBreakageCheck()) {
    return;
  }
  if (matsuuraTailstockActive) {
    if (useMatsuuraPostCutRerunRecovery()) {
      error("Post-cut sister-tool rerun cannot be deferred across TAILSTOCK_OFF. Use Broken tool action = Alarm and stop, or disable the tailstock Actions for this proof.");
      return;
    }
    if (matsuuraTailstockDeferredPostCutTool) {
      error("A deferred post-cut tool check is waiting for TAILSTOCK_OFF. Place TAILSTOCK_OFF immediately after the supported operation before starting another operation.");
      return;
    }
    matsuuraTailstockDeferredPostCutTool = tool;
    writeComment("POST-CUT TOOL BREAKAGE CHECK DEFERRED UNTIL TAILSTOCK OFF T" + formatMatsuuraToolLengthAutomationInteger(tool.number));
    return;
  }
  writeMatsuuraPostCutToolBreakageCheckForTool(tool);
}

function writeMatsuuraDeferredTailstockPostCutToolBreakageCheck() {
  if (!matsuuraTailstockDeferredPostCutTool) {
    return;
  }
  if (matsuuraTailstockActive) {
    error("Deferred post-cut tool checking cannot run until M122 has retracted the tailstock.");
    return;
  }
  var checkTool = matsuuraTailstockDeferredPostCutTool;
  matsuuraTailstockDeferredPostCutTool = undefined;
  writeMatsuuraPostCutToolBreakageCheckForTool(checkTool);
}

function finalizeMatsuuraToolLengthAutomationOutput() {
  forceModals();
  forceXYZ();
  forceABC();
  forceFeed();
}

function writeMatsuuraToolLengthAutomationAtProgramStart() {
  var writeSet = getProperty("matsuuraToolLengthSetMode") == "allAtProgramStart";
  var writeCheck = getProperty("matsuuraToolBreakageCheckMode") == "allAtProgramStart";
  if (!writeSet && !writeCheck) {
    return;
  }
  var tools = getMatsuuraToolLengthAutomationTools();
  if (tools.length == 0) {
    return;
  }
  writeln("");
  writeComment("TOOL LENGTH AUTOMATION - PROGRAM START");
  writeMatsuuraToolLengthAutomationSafeModal();
  for (var i = 0; i < tools.length; ++i) {
    validateMatsuuraToolLengthAutomationTool(tools[i]);
    if (writeSet) {
      writeMatsuuraToolLengthSetCall(tools[i]);
      matsuuraToolLengthSetTools[getMatsuuraToolLengthAutomationKey(tools[i])] = true;
    }
    if (writeCheck) {
      writeMatsuuraToolBreakageCheckCall(tools[i], undefined, false, true);
      matsuuraToolBreakageCheckedTools[getMatsuuraToolLengthAutomationKey(tools[i])] = true;
    }
  }
  finalizeMatsuuraToolLengthAutomationOutput();
}

function shouldWriteMatsuuraToolLengthAutomationForSection(mode, tool, insertToolCall, trackedTools) {
  if (mode == "everyToolChange") {
    return insertToolCall || isFirstSection();
  }
  if (mode == "beforeFirstUse") {
    var key = getMatsuuraToolLengthAutomationKey(tool);
    if (trackedTools[key]) {
      return false;
    }
    trackedTools[key] = true;
    return true;
  }
  return false;
}

function writeMatsuuraToolLengthAutomationForSection(tool, insertToolCall) {
  if (!isMatsuuraToolLengthAutomationTool(tool)) {
    return;
  }
  var writeSet = shouldWriteMatsuuraToolLengthAutomationForSection(getProperty("matsuuraToolLengthSetMode"), tool, insertToolCall, matsuuraToolLengthSetTools);
  var writeCheck = shouldWriteMatsuuraToolLengthAutomationForSection(getProperty("matsuuraToolBreakageCheckMode"), tool, insertToolCall, matsuuraToolBreakageCheckedTools);
  if (!writeSet && !writeCheck) {
    return;
  }
  validateMatsuuraToolLengthAutomationTool(tool);
  writeln("");
  writeComment("TOOL LENGTH AUTOMATION - SECTION");
  writeMatsuuraToolLengthAutomationSafeModal();
  if (writeSet) {
    writeMatsuuraToolLengthSetCall(tool);
  }
  if (writeCheck) {
    writeMatsuuraToolBreakageCheckCall(tool, undefined, true, false);
  }
  finalizeMatsuuraToolLengthAutomationOutput();
}

function isMatsuuraTCPOutputSection(_section) {
  return typeof isTCPSupportedByOperation == "function" && isTCPSupportedByOperation(_section);
}

function getMatsuuraTCPSmoothingLevel(baseLevel) {
  var tcpSmoothingLevel = getProperty("tcpSmoothingLevel");
  if (tcpSmoothingLevel == "auto") {
    return baseLevel; // preserve the proven G131 F-level behavior until R-level use is verified.
  }
  var level = parseInt(tcpSmoothingLevel, 10);
  return isNaN(level) ? baseLevel : level;
}

function setSmoothing(mode) {
  smoothingSettings = settings.smoothing;
  if (mode == smoothing.isActive && (!mode || !smoothing.isDifferent) && !smoothing.force) {
    return; // return if smoothing is already active or is not different
  }
  if (validateLengthCompensation && smoothingSettings.cancelCompensation) {
    validate(!state.lengthCompensationActive, "Length compensation is active while trying to update smoothing.");
  }

  if (mode) { // enable smoothing
    writeBlock(gFormat.format(131), smoothing.prefix + smoothing.level);
  } else { // disable smoothing
    writeBlock(gFormat.format(130));
  }
  smoothing.isActive = mode;
  smoothing.force = false;
  smoothing.isDifferent = false;
}

function onSection() {
  var forceSectionRestart = optionalSection && !currentSection.isOptional();
  var forceMatsuuraProbeCAngleFullReinit = matsuuraProbeForceFullReinitAfterCAngle;
  matsuuraProbeForceFullReinitAfterCAngle = false;
  optionalSection = currentSection.isOptional();
  var insertToolCall = isToolChangeNeeded("number") || forceSectionRestart;
  validateMatsuuraTailstockSection(currentSection, insertToolCall);
  var newWorkOffset = isNewWorkOffset() || forceSectionRestart;
  var newWorkPlane = isNewWorkPlane() || forceSectionRestart || (typeof defineWorkPlane == "function" &&
    Vector.diff(defineWorkPlane(getPreviousSection(), false), defineWorkPlane(currentSection, false)).length > 1e-4);
  var delaySpindleForMatsuuraTailstock = matsuuraTailstockPending || (matsuuraTailstockActive && newWorkPlane);
  operationNeedsSafeStart = getProperty("safeStartAllOperations") && !isFirstSection();

  initializeSmoothingPrefix();
  initializeSmoothing(); // initialize smoothing mode

  if (insertToolCall || newWorkOffset || newWorkPlane || smoothing.cancel || state.tcpIsActive || currentSection.isMultiAxis()) {
    if (insertToolCall && !isFirstSection()) {
      onCommand(COMMAND_COOLANT_OFF); // turn off coolant before retract during tool change
      onCommand(COMMAND_STOP_SPINDLE); // stop spindle before retract during tool change
    }
    if (state.tcpIsActive) {
      disableLengthCompensation(true, true); // cancel TCP before any machine-coordinate retract
    }
    writeRetract(Z); // retract
    disableLengthCompensation();
    if (isFirstSection()) {
      cancelWorkPlane(true);
      if (machineConfiguration.isMultiAxisConfiguration()) {
        positionABC(new Vector(0, 0, 0));
      }
      forceABC();
    } else {
      if (insertToolCall || newWorkPlane || smoothing.cancel) {
        cancelWorkPlane();
      }
      if (insertToolCall || smoothing.cancel) {
        setSmoothing(false);
      }
    }
  }

  writeMatsuuraPostCutRerunBegin(tool);
  writeln("");
  writeComment(getParameter("operation-comment", ""));

  if (getProperty("showNotes")) {
    writeSectionNotes();
  }

  // tool change
  writeToolCall(tool, insertToolCall);
  writeMatsuuraToolLengthAutomationForSection(tool, insertToolCall);
  if (delaySpindleForMatsuuraTailstock) {
    onCommand(COMMAND_COOLANT_OFF);
    onCommand(COMMAND_STOP_SPINDLE);
    forceSpindleSpeed = true;
    forceCoolant = true;
  } else if (!isTappingCycle() || (getProperty("useRigidTapping") == "no")) {
    startSpindle(tool, insertToolCall);
  }
  // write parametric feedrate table
  if (typeof initializeParametricFeeds == "function") {
    initializeParametricFeeds(insertToolCall);
  }
  // Output modal commands here
  writeBlock(gAbsIncModal.format(90), gFeedModeModal.format(getProperty("useG95") ? 95 : 94), gPlaneModal.format(17));

  // set wcs
  var wcsIsRequired = true;
  if (insertToolCall || operationNeedsSafeStart) {
    currentWorkOffset = undefined; // force work offset when changing tool
    wcsIsRequired = newWorkOffset || insertToolCall || !operationNeedsSafeStart || getPreviousSection().strategy == "probe";
  }
  writeWCS(currentSection, wcsIsRequired);

  forceXYZ();

  onCommand(COMMAND_START_CHIP_TRANSPORT);

  var matsuuraPreviousABC = getCurrentDirection();
  var abc = defineWorkPlane(currentSection, !machineConfiguration.isHeadConfiguration());
  if (forceMatsuuraProbeCAngleFullReinit) {
    forceWorkPlane();
    forceABC();
    setWorkPlane(abc);
  }
  setRotaryClampForCurrentSection(currentSection);

  if (delaySpindleForMatsuuraTailstock && (!isTappingCycle() || (getProperty("useRigidTapping") == "no"))) {
    startSpindle(tool, true);
  }

  setProbeAngle(); // output probe angle rotations if required

  setCoolant(tool.coolant); // writes the required coolant codes

  setSmoothing(smoothing.isAllowed); // writes the required smoothing codes

  var matsuuraProbeOnAlreadyActiveForSection = false;
  if (matsuuraProbeOnContinuesToNextSection) {
    matsuuraProbeOnAlreadyActiveForSection = prepareMatsuuraProbeOnForSectionStart();
  }

  // prepositioning
  var initialPosition = getFramePosition(currentSection.getInitialPosition());
  var isRequired = insertToolCall || state.retractedZ || !state.lengthCompensationActive || (!isFirstSection() && getPreviousSection().isMultiAxis());
  writeInitialPositioning(initialPosition, isRequired, undefined, undefined, matsuuraPreviousABC);

  if (isProbeOperation()) {
    validate(probeVariables.probeAngleMethod != "G68", "You cannot probe while G68 Rotation is in effect.");
    validate(probeVariables.probeAngleMethod != "G54.4", "You cannot probe while workpiece setting error compensation G54.4 is enabled.");
    if (useMatsuuraProbingMacros()) {
      validate(!printProbeResults(), "Matsuura probing output does not support Fusion print results yet.");
      if (!matsuuraProbeOnAlreadyActiveForSection) {
        writeBlock(mFormat.format(108)); // probe on
      }
    } else {
      matsuuraProbeOnContinuesToNextSection = false;
      matsuuraProbeContinuationMacroFamily = "";
      writeBlock(gFormat.format(65), "P" + (probeBaseNumber + 32)); // spin the probe on
      inspectionCreateResultsFileHeader();
    }
  } else if (isInspectionOperation() && (typeof inspectionProcessSectionStart == "function")) {
    inspectionProcessSectionStart();
  }

  if (subprogramsAreSupported()) {
    subprogramDefine(initialPosition, abc); // define subprogram
  }
  state.retractedZ = false;
}

function onDwell(seconds) {
  var maxValue = 99999.999;
  if (seconds > maxValue) {
    warning(subst(localize("Dwelling time of '%1' exceeds the maximum value of '%2' in operation '%3'"), seconds, maxValue, getParameter("operation-comment", "")));
  }
  milliseconds = clamp(1, seconds * 1000, 99999999);
  var saveFeedMode = gFeedModeModal.getCurrent();
  writeBlock(gFeedModeModal.format(94), gFormat.format(4), "P" + milliFormat.format(milliseconds));
  writeBlock(gFeedModeModal.format(saveFeedMode));
}

function onSpindleSpeed(spindleSpeed) {
  writeBlock(sOutput.format(spindleSpeed));
}

function onCycle() {
  gRetractModal.reset(); // force G98/G99 at the start of each new canned-cycle operation
  writeBlock(gPlaneModal.format(17));
}

function getCycleTypeName() {
  if (typeof cycleType != "undefined") {
    return cycleType;
  }
  if ((typeof cycle != "undefined") && cycle) {
    if (cycle.type) {
      return cycle.type;
    }
    if (cycle.cycleType) {
      return cycle.cycleType;
    }
  }
  if ((typeof hasParameter == "function") && hasParameter("operation:cycleType")) {
    return getParameter("operation:cycleType");
  }
  return "";
}

function shouldExpandDrillingCycle() {
  // Production default uses proven normal-drill canned cycles; setting this off forces expanded fallback output.
  switch (getCycleTypeName()) {
  case "drilling":
  case "counter-boring":
  case "chip-breaking":
  case "deep-drilling":
    return !getProperty("allowDrillingCannedCyclesProof");
  default:
    return false;
  }
}

function forceMotionCodeForExpandedDrilling() {
  if ((typeof cycleExpanded != "undefined") && cycleExpanded && shouldExpandDrillingCycle()) {
    gMotionModal.reset();
  }
}

function writeDrillCycle(cycle, x, y, z) {
  var cycleTypeName = getCycleTypeName();
  if (shouldExpandDrillingCycle()) {
    expandCyclePoint(x, y, z);
    return;
  }
  if (!isSameDirection(machineConfiguration.getSpindleAxis(), getForwardDirection(currentSection))) {
    expandCyclePoint(x, y, z);
    return;
  }
  if (isFirstCyclePoint()) {
    // return to initial Z which is clearance plane and set absolute mode
    repositionToCycleClearance(cycle, x, y, z);

    writeBlock(gFeedModeModal.format(getProperty("useG95") || (isTappingCycle() && getProperty("usePitchForTapping")) ? 95 : 94));
    var F = getProperty("useG95") ? (cycle.feedrate / spindleSpeed) : cycle.feedrate;
    var P = !cycle.dwell ? 0 : clamp(1, cycle.dwell * 1000, 99999999); // in milliseconds
    switch (cycleTypeName) {
    case "drilling":
      writeBlock(
        gRetractModal.format(98), gCycleModal.format(81),
        getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
        feedOutput.format(F)
      );
      break;
    case "counter-boring":
      if (P > 0) {
        writeBlock(
          gRetractModal.format(98), gCycleModal.format(82),
          getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
          "P" + milliFormat.format(P),
          feedOutput.format(F)
        );
      } else {
        writeBlock(
          gRetractModal.format(98), gCycleModal.format(81),
          getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
          feedOutput.format(F)
        );
      }
      break;
    case "chip-breaking":
      if ((cycle.accumulatedDepth < cycle.depth) || (P > 0)) {
        expandCyclePoint(x, y, z);
      } else {
        writeBlock(
          gRetractModal.format(98), gCycleModal.format(73),
          getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
          peckOutput.format(cycle.incrementalDepth),
          feedOutput.format(F)
        );
      }
      break;
    case "deep-drilling":
      if (P > 0) {
        expandCyclePoint(x, y, z);
      } else {
        writeBlock(
          gRetractModal.format(98), gCycleModal.format(83),
          getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
          peckOutput.format(cycle.incrementalDepth),
          // conditional(P > 0, "P" + milliFormat.format(P)),
          feedOutput.format(F)
        );
      }
      break;
    case "tapping":
    case "left-tapping":
    case "right-tapping":
      if (getProperty("useRigidTapping") != "no") {
        writeBlock(mFormat.format(80), sOutput.format(spindleSpeed));
      }
      var cycleCode = (cycleTypeName == "left-tapping" || (cycleTypeName == "tapping" && tool.type == TOOL_TAP_LEFT_HAND)) ? 74 : 84;
      var tappingFPM = tool.getThreadPitch() * rpmFormat.getResultingValue(spindleSpeed);
      F = (getProperty("useG95") || getProperty("usePitchForTapping") ? tool.getThreadPitch() : tappingFPM);
      writeBlock(
        gRetractModal.format(98), gCycleModal.format(cycleCode),
        getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
        "P" + milliFormat.format(P),
        getProperty("usePitchForTapping") ? pitchOutput.format(F) : feedOutput.format(F)
      );
      forceFeed();
      break;
    case "tapping-with-chip-breaking":
    case "left-tapping-with-chip-breaking":
    case "right-tapping-with-chip-breaking":
      if (getProperty("useRigidTapping") != "no") {
        writeBlock(mFormat.format(80), sOutput.format(spindleSpeed));
      }
      var cycleCode = (cycleTypeName == "left-tapping-with-chip-breaking" || (cycleTypeName == "tapping-with-chip-breaking" && tool.type == TOOL_TAP_LEFT_HAND)) ? 74 : 84;
      var tappingFPM = tool.getThreadPitch() * rpmFormat.getResultingValue(spindleSpeed);
      F = (getProperty("useG95") || getProperty("usePitchForTapping") ? tool.getThreadPitch() : tappingFPM);
      writeBlock(
        gRetractModal.format(98), gCycleModal.format(cycleCode),
        getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
        "P" + milliFormat.format(P),
        conditional(cycle.incrementalDepth > 0, peckOutput.format(cycle.incrementalDepth)),
        getProperty("usePitchForTapping") ? pitchOutput.format(F) : feedOutput.format(F)
      );
      forceFeed();
      break;
    case "fine-boring":
      writeBlock(
        gRetractModal.format(98), gCycleModal.format(76),
        getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
        "P" + milliFormat.format(P), // not optional
        "Q" + xyzFormat.format(cycle.shift),
        feedOutput.format(F)
      );
      break;
    case "back-boring":
      var dx = (gPlaneModal.getCurrent() == 19) ? cycle.backBoreDistance : 0;
      var dy = (gPlaneModal.getCurrent() == 18) ? cycle.backBoreDistance : 0;
      var dz = (gPlaneModal.getCurrent() == 17) ? cycle.backBoreDistance : 0;
      writeBlock(
        gRetractModal.format(98), gCycleModal.format(87),
        getCommonCycle(x - dx, y - dy, z - dz, cycle.bottom, cycle.clearance),
        "Q" + xyzFormat.format(cycle.shift),
        "P" + milliFormat.format(P), // not optional
        feedOutput.format(F)
      );
      break;
    case "reaming":
      if (feedFormat.getResultingValue(cycle.feedrate) != feedFormat.getResultingValue(cycle.retractFeedrate)) {
        expandCyclePoint(x, y, z);
        break;
      }
      if (P > 0) {
        writeBlock(
          gRetractModal.format(98), gCycleModal.format(89),
          getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
          "P" + milliFormat.format(P),
          feedOutput.format(F)
        );
      } else {
        writeBlock(
          gRetractModal.format(98), gCycleModal.format(85),
          getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
          feedOutput.format(F)
        );
      }
      break;
    case "stop-boring":
      if (P > 0) {
        expandCyclePoint(x, y, z);
      } else {
        writeBlock(
          gRetractModal.format(98), gCycleModal.format(86),
          getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
          feedOutput.format(F)
        );
      }
      break;
    case "manual-boring":
      writeBlock(
        gRetractModal.format(98), gCycleModal.format(88),
        getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
        "P" + milliFormat.format(P), // not optional
        feedOutput.format(F)
      );
      break;
    case "boring":
      if (feedFormat.getResultingValue(cycle.feedrate) != feedFormat.getResultingValue(cycle.retractFeedrate)) {
        expandCyclePoint(x, y, z);
        break;
      }
      if (P > 0) {
        writeBlock(
          gRetractModal.format(98), gCycleModal.format(89),
          getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
          "P" + milliFormat.format(P), // not optional
          feedOutput.format(F)
        );
      } else {
        writeBlock(
          gRetractModal.format(98), gCycleModal.format(85),
          getCommonCycle(x, y, z, cycle.retract, cycle.clearance),
          feedOutput.format(F)
        );
      }
      break;
    default:
      expandCyclePoint(x, y, z);
    }
    if (subprogramsAreSupported()) {
      // place cycle operation in subprogram
      handleCycleSubprogram(new Vector(x, y, z), new Vector(0, 0, 0), false);
      if (subprogramState.incrementalMode) { // set current position to clearance height
        setCyclePosition(cycle.clearance);
      }
    }
  } else {
    if (cycleExpanded) {
      expandCyclePoint(x, y, z);
    } else {
      if (!xyzFormat.areDifferent(x, xOutput.getCurrent()) &&
          !xyzFormat.areDifferent(y, yOutput.getCurrent()) &&
          !xyzFormat.areDifferent(z, zOutput.getCurrent())) {
        switch (gPlaneModal.getCurrent()) {
        case 17: // XY
          xOutput.reset(); // at least one axis is required
          break;
        case 18: // ZX
          zOutput.reset(); // at least one axis is required
          break;
        case 19: // YZ
          yOutput.reset(); // at least one axis is required
          break;
        }
      }
      if (subprogramsAreSupported() && subprogramState.incrementalMode) { // set current position to retract height
        setCyclePosition(cycle.retract);
      }
      if ((currentSection.getPolarMode && currentSection.getPolarMode() != POLAR_MODE_OFF) && currentSection.isMultiAxis()) {
        var polarPosition = getPolarPosition(x, y, z);
        setCurrentPositionAndDirection(polarPosition);
        writeBlock(xOutput.format(polarPosition.first.x), yOutput.format(polarPosition.first.y), zOutput.format(polarPosition.first.z),
          aOutput.format(polarPosition.second.x), bOutput.format(polarPosition.second.y), cOutput.format(polarPosition.second.z));
      } else {
        writeBlock(xOutput.format(x), yOutput.format(y), zOutput.format(z));
      }
      if (subprogramsAreSupported() && subprogramState.incrementalMode) { // set current position to clearance height
        setCyclePosition(cycle.clearance);
      }
    }
  }
}

function getCommonCycle(x, y, z, r, c) {
  forceXYZ(); // force xyz on first drill hole of any cycle
  if ((currentSection.getPolarMode && currentSection.getPolarMode() != POLAR_MODE_OFF) && currentSection.isMultiAxis()) {
    var polarPosition = getPolarPosition(x, y, z);
    return [xOutput.format(polarPosition.first.x), yOutput.format(polarPosition.first.y), zOutput.format(polarPosition.first.z),
      aOutput.format(polarPosition.second.x), bOutput.format(polarPosition.second.y), cOutput.format(polarPosition.second.z),
      "R" + xyzFormat.format(r)];
  } else {
    if (subprogramsAreSupported() && subprogramState.incrementalMode) {
      zOutput.format(c);
      return [xOutput.format(x), yOutput.format(y), "Z" + xyzFormat.format(z - r), "R" + xyzFormat.format(r - c)];
    } else {
      return [xOutput.format(x), yOutput.format(y), zOutput.format(z), "R" + xyzFormat.format(r)];
    }
  }
}

function useMatsuuraProbingMacros() {
  return true;
}

function getMatsuuraProbeProperty(propertyName, minimumValue) {
  var value = getProperty(propertyName);
  validate(isFinite(value) && (value > minimumValue), propertyName + " must be greater than " + minimumValue + " for Matsuura probing.");
  return value;
}

function getMatsuuraProbeDiameter() {
  var diameter = getProperty("matsuuraProbeDiameter");
  if (diameter == 0) {
    diameter = tool.diameter;
  }
  validate(isFinite(diameter) && (diameter > 0), "Matsuura probe diameter #508 must be greater than 0.");
  return diameter;
}

function getMatsuuraProbeApproachDistance(cycle) {
  var distance = getProperty("matsuuraProbeApproachDistanceOverride");
  if (distance == 0) {
    distance = cycle.probeOvertravel;
  }
  validate(isFinite(distance) && (distance > 0), "Matsuura probe approach #504 must be greater than 0.");
  return distance;
}

function getMatsuuraProbeMeasureFeed(cycle) {
  var feed = getProperty("matsuuraProbeMeasureFeedOverride");
  if (feed == 0) {
    var fusionMeasureFeed = ((typeof hasParameter == "function") && hasParameter("operation:tool_feedProbeMeasure")) ? getParameter("operation:tool_feedProbeMeasure") : undefined;
    feed = isFinite(fusionMeasureFeed) && (fusionMeasureFeed > 0) ? fusionMeasureFeed :
      (isFinite(cycle.measureFeed) && (cycle.measureFeed > 0) ? cycle.measureFeed : cycle.feedrate);
  }
  validate(isFinite(feed) && (feed > 0), "Matsuura probe measure feed #505 must be greater than 0.");
  return feed;
}

function getFusionHighFeedrateFallback(cycle) {
  var fusionLeadInFeed = ((typeof hasParameter == "function") && hasParameter("operation:tool_feedEntry")) ? getParameter("operation:tool_feedEntry") : undefined;
  if (isFinite(fusionLeadInFeed) && (fusionLeadInFeed > 0)) {
    return fusionLeadInFeed;
  }
  if ((typeof hasParameter == "function") && hasParameter("operation:highFeedrate")) {
    var highFeedrateMode = hasParameter("operation:highFeedrateMode") ? getParameter("operation:highFeedrateMode") : "";
    var fusionHighFeedrate = getParameter("operation:highFeedrate");
    if ((highFeedrateMode != "disabled") && isFinite(fusionHighFeedrate) && (fusionHighFeedrate > 0)) {
      return fusionHighFeedrate;
    }
  }
  return cycle.feedrate;
}

function getMatsuuraProbeFastFeed(cycle) {
  var feed = getProperty("matsuuraProbeFastFeedOverride");
  if (feed == 0) {
    feed = getFusionHighFeedrateFallback(cycle);
  }
  validate(isFinite(feed) && (feed > 0), "Matsuura probe fast feed #506 must be greater than 0.");
  return feed;
}

function writeMatsuuraProbeSettings(cycle) {
  writeBlock("#504=" + xyzFormat.format(getMatsuuraProbeApproachDistance(cycle)));
  writeBlock("#505=" + xyzFormat.format(getMatsuuraProbeMeasureFeed(cycle)));
  writeBlock("#506=" + xyzFormat.format(getMatsuuraProbeFastFeed(cycle)));
  writeBlock("#508=" + xyzFormat.format(getMatsuuraProbeDiameter()));
}

function getMatsuuraProbeWorkOffset() {
  var probeWorkOffset = currentSection.probeWorkOffset || currentSection.workOffset || 1;
  validateMatsuuraProbeWorkOffset(probeWorkOffset, "Matsuura probing output");
  return probeWorkOffset;
}

function getMatsuuraProbeDrivingWorkOffset() {
  var drivingWorkOffset = currentSection.workOffset || 1;
  validateMatsuuraProbeWorkOffset(drivingWorkOffset, "Matsuura probing driving WCS");
  return drivingWorkOffset;
}

function isMatsuuraProbeDrivingWorkOffsetOverridden() {
  return getMatsuuraProbeDrivingWorkOffset() != getMatsuuraProbeWorkOffset();
}

function validateMatsuuraProbeWorkOffset(workOffset, label) {
  validate(isFinite(workOffset) && (Math.floor(workOffset) == workOffset) && (workOffset >= 1) && (workOffset <= 306), label + " supports only G54-G59 and G54.1 P1-P300.");
}

function getMatsuuraProbeWorkOffsetVariable(workOffset, axisIndex) {
  validateMatsuuraProbeWorkOffset(workOffset, "Matsuura probing WCS variable mapping");
  validate(isFinite(axisIndex) && (Math.floor(axisIndex) == axisIndex) && (axisIndex >= 1) && (axisIndex <= 20), "Matsuura probing WCS variable axis must be 1-20.");
  if (workOffset <= 6) {
    return 5220 + axisIndex + (workOffset - 1) * 20;
  }
  var additionalWorkOffset = workOffset - 6; // Fusion work offset 7 == G54.1 P1.
  if (additionalWorkOffset <= 48) {
    return 7000 + axisIndex + (additionalWorkOffset - 1) * 20;
  }
  return 14000 + axisIndex + (additionalWorkOffset - 1) * 20;
}

function getMatsuuraProbeSelectedXVariable() {
  return getMatsuuraProbeWorkOffsetVariable(getMatsuuraProbeWorkOffset(), 1);
}

function getMatsuuraProbeSelectedYVariable() {
  return getMatsuuraProbeWorkOffsetVariable(getMatsuuraProbeWorkOffset(), 2);
}

function getMatsuuraProbeSelectedZVariable() {
  return getMatsuuraProbeWorkOffsetVariable(getMatsuuraProbeWorkOffset(), 3);
}

function getMatsuuraProbeDrivingXVariable() {
  return getMatsuuraProbeWorkOffsetVariable(getMatsuuraProbeDrivingWorkOffset(), 1);
}

function getMatsuuraProbeDrivingYVariable() {
  return getMatsuuraProbeWorkOffsetVariable(getMatsuuraProbeDrivingWorkOffset(), 2);
}

function getMatsuuraProbeDrivingZVariable() {
  return getMatsuuraProbeWorkOffsetVariable(getMatsuuraProbeDrivingWorkOffset(), 3);
}

function writeMatsuuraProbeDrivingWorkOffset() {
  var drivingWorkOffset = getMatsuuraProbeDrivingWorkOffset();
  if (drivingWorkOffset <= 6) {
    writeBlock(gFormat.format(53 + drivingWorkOffset));
  } else {
    writeBlock("G54.1", "P" + (drivingWorkOffset - 6));
  }
  currentWorkOffset = drivingWorkOffset;
}

function formatMatsuuraProbeWorkOffsetName(workOffset) {
  validateMatsuuraProbeWorkOffset(workOffset, "Matsuura probing WCS name");
  return workOffset <= 6 ? "G" + (53 + workOffset) : "G54.1 P" + (workOffset - 6);
}

// After a probe transfer/touch, route the next XY move through full section clearance.
var matsuuraProbePendingXYReturnAfterTransfer = false;
var matsuuraProbePendingP8600ClearanceBeforeXY = false;
var matsuuraProbePendingCAngleClearanceBeforeXY = false;
var matsuuraProbeSuppressCAngleReturnRapid = false;
var matsuuraProbeSkipCAngleCycleRetract = false;
var matsuuraProbeForceFullReinitAfterCAngle = false;
var matsuuraProbeOnContinuesToNextSection = false;
var matsuuraProbeContinuationMacroFamily = "";

function getMatsuuraProbeSectionParameter(section, name) {
  if (!section || (typeof section.getParameter != "function")) {
    return undefined;
  }
  if ((typeof section.hasParameter == "function") && section.hasParameter(name)) {
    return section.getParameter(name);
  }
  try {
    return section.getParameter(name);
  } catch (e) {
    return undefined;
  }
}

function getMatsuuraProbeSectionCycleTypeName(section) {
  if (!section) {
    return "";
  }
  if ((section == currentSection) && (typeof getCycleTypeName == "function")) {
    var cycleTypeName = getCycleTypeName();
    if (cycleTypeName) {
      return cycleTypeName;
    }
  }
  if (typeof section.hasCycle == "function") {
    var knownCycleTypes = [
      "probing-z",
      "probing-xy-circular-hole",
      "probing-xy-circular-boss",
      "probing-xy-rectangular-hole",
      "probing-xy-rectangular-boss",
      "probing-x-channel",
      "probing-y-channel",
      "probing-x-channel-with-island",
      "probing-y-channel-with-island"
    ];
    for (var i = 0; i < knownCycleTypes.length; ++i) {
      if (section.hasCycle(knownCycleTypes[i])) {
        return knownCycleTypes[i];
      }
    }
  }
  if ((typeof section.hasParameter == "function") && section.hasParameter("operation:cycleType")) {
    return section.getParameter("operation:cycleType");
  }
  return getMatsuuraProbeSectionParameter(section, "operation:cycleType") || "";
}

function getMatsuuraProbeCenterMacroFamily(section) {
  switch (getMatsuuraProbeSectionCycleTypeName(section)) {
  case "probing-xy-circular-hole":
    return "P8200";
  case "probing-xy-circular-boss":
    return "P8210";
  case "probing-xy-rectangular-hole":
    return "P8400";
  case "probing-xy-rectangular-boss":
    return "P8410";
  case "probing-x-channel":
  case "probing-y-channel":
    return "P8430";
  case "probing-x-channel-with-island":
  case "probing-y-channel-with-island":
    return "P8420";
  default:
    return "";
  }
}

function getMatsuuraProbeTopPlaneMacroFamily(section) {
  var centerMacroFamily = getMatsuuraProbeCenterMacroFamily(section);
  if (centerMacroFamily) {
    return centerMacroFamily;
  }
  return getMatsuuraProbeSectionCycleTypeName(section) == "probing-z" ? "P8300" : "";
}

function getMatsuuraProbeSectionWorkOffset(section) {
  var workOffset = section.probeWorkOffset || section.workOffset || 1;
  return workOffset == 0 ? 1 : workOffset;
}

function getMatsuuraProbeSectionToolKey(section) {
  var sectionTool = section.getTool();
  return Math.round(sectionTool.number) + ":" + Math.round(sectionTool.lengthOffset);
}

function areMatsuuraProbeSectionWorkPlanesSame(firstSection, secondSection) {
  return Vector.diff(defineWorkPlane(firstSection, false), defineWorkPlane(secondSection, false)).length <= 1e-4;
}

function isMatsuuraProbeNextSectionAtCurrentPosition(nextSection) {
  var currentPosition = getCurrentPosition();
  var nextPosition = getFramePosition(nextSection.getInitialPosition());
  if (!currentPosition || !nextPosition ||
      !isFinite(currentPosition.x) || !isFinite(currentPosition.y) || !isFinite(currentPosition.z) ||
      !isFinite(nextPosition.x) || !isFinite(nextPosition.y) || !isFinite(nextPosition.z)) {
    return false;
  }
  return xyzFormat.getResultingValue(currentPosition.x) == xyzFormat.getResultingValue(nextPosition.x) &&
    xyzFormat.getResultingValue(currentPosition.y) == xyzFormat.getResultingValue(nextPosition.y) &&
    xyzFormat.getResultingValue(currentPosition.z) == xyzFormat.getResultingValue(nextPosition.z);
}

function shouldDeferMatsuuraProbeOffForNextSection() {
  if (!useMatsuuraProbingMacros() || !isProbeOperation() || isLastSection() || getProperty("safeStartAllOperations")) {
    return false;
  }
  var nextSection = getNextSection();
  if (!isProbeOperation(nextSection) || currentSection.isMultiAxis() || nextSection.isMultiAxis()) {
    return false;
  }
  if (currentSection.isOptional() != nextSection.isOptional()) {
    return false;
  }
  if (getMatsuuraProbeSectionToolKey(currentSection) != getMatsuuraProbeSectionToolKey(nextSection)) {
    return false;
  }
  if (getMatsuuraProbeSectionWorkOffset(currentSection) != getMatsuuraProbeSectionWorkOffset(nextSection)) {
    return false;
  }
  if (!areMatsuuraProbeSectionWorkPlanesSame(currentSection, nextSection)) {
    return false;
  }
  var currentCenterMacroFamily = getMatsuuraProbeCenterMacroFamily(currentSection);
  if (currentCenterMacroFamily && (currentCenterMacroFamily == getMatsuuraProbeCenterMacroFamily(nextSection))) {
    return currentCenterMacroFamily;
  }
  if (getMatsuuraProbeTopPlaneMacroFamily(currentSection) &&
      getMatsuuraProbeTopPlaneMacroFamily(nextSection) &&
      isMatsuuraProbeNextSectionAtCurrentPosition(nextSection)) {
    return "SAME_POSITION";
  }
  return false;
}

function prepareMatsuuraProbeOnForSectionStart() {
  if (!matsuuraProbeOnContinuesToNextSection) {
    return false;
  }
  var previousMacroFamily = matsuuraProbeContinuationMacroFamily;
  matsuuraProbeOnContinuesToNextSection = false;
  matsuuraProbeContinuationMacroFamily = "";
  if (previousMacroFamily == "SAME_POSITION") {
    return true;
  }
  if (previousMacroFamily && (previousMacroFamily == getMatsuuraProbeCenterMacroFamily(currentSection))) {
    return true;
  }
  writeBlock(mFormat.format(109)); // probe off before this section repositions
  return false;
}

function getMatsuuraProbeSectionClearanceZ(fallbackZ) {
  var safeZ = fallbackZ;
  if (typeof currentSection != "undefined" && currentSection) {
    var initialPosition = getFramePosition(currentSection.getInitialPosition());
    if (initialPosition && isFinite(initialPosition.z)) {
      safeZ = Math.max(safeZ, initialPosition.z);
    }
  }
  return safeZ;
}

function isMatsuuraRapidXYMoveFromCurrent(_x, _y, currentPosition) {
  if (!currentPosition) {
    return false;
  }
  return (isFinite(_x) && (xyzFormat.getResultingValue(_x) != xyzFormat.getResultingValue(currentPosition.x))) ||
    (isFinite(_y) && (xyzFormat.getResultingValue(_y) != xyzFormat.getResultingValue(currentPosition.y)));
}

function forceMatsuuraProbeAbsoluteRapidModals() {
  gAbsIncModal.reset();
  gMotionModal.reset();
}

function writeMatsuuraProbeFullClearanceXYMove(_x, _y, _z) {
  writeMatsuuraProbeDrivingWorkOffset();
  var clearanceZ = getMatsuuraProbeSectionClearanceZ(_z);
  var currentPosition = getCurrentPosition();
  if (currentPosition && isFinite(currentPosition.z) && (xyzFormat.getResultingValue(currentPosition.z) < xyzFormat.getResultingValue(clearanceZ))) {
    var clearanceWord = zOutput.format(clearanceZ);
    if (clearanceWord) {
      forceMatsuuraProbeAbsoluteRapidModals();
      writeBlock(gAbsIncModal.format(90), gMotionModal.format(0), clearanceWord);
    }
  }
  xOutput.reset();
  yOutput.reset();
  var x = xOutput.format(_x);
  var y = yOutput.format(_y);
  if (x || y) {
    forceMatsuuraProbeAbsoluteRapidModals();
    writeBlock(gAbsIncModal.format(90), gMotionModal.format(0), x, y);
  }
  if (isFinite(_z) && (xyzFormat.getResultingValue(_z) < xyzFormat.getResultingValue(clearanceZ))) {
    var targetZ = zOutput.format(_z);
    if (targetZ) {
      forceMatsuuraProbeAbsoluteRapidModals();
      writeBlock(gAbsIncModal.format(90), gMotionModal.format(0), targetZ);
    }
  }
  if (x || y) {
    forceFeed();
  }
}

function writeMatsuuraProbeBeginXYTransferIfNeeded() {
  if (!isMatsuuraProbeDrivingWorkOffsetOverridden()) {
    return;
  }
  writeBlock("#590=#" + getMatsuuraProbeDrivingXVariable());
  writeBlock("#591=#" + getMatsuuraProbeDrivingYVariable());
}

function writeMatsuuraProbeEndXYTransferIfNeeded(transferX, transferY) {
  if (!isMatsuuraProbeDrivingWorkOffsetOverridden()) {
    return;
  }
  transferX = transferX !== false;
  transferY = transferY !== false;
  var drivingXVariable = getMatsuuraProbeDrivingXVariable();
  var drivingYVariable = getMatsuuraProbeDrivingYVariable();
  var selectedXVariable = getMatsuuraProbeSelectedXVariable();
  var selectedYVariable = getMatsuuraProbeSelectedYVariable();
  if (transferX) {
    writeBlock("#592=#" + drivingXVariable);
  }
  if (transferY) {
    writeBlock("#593=#" + drivingYVariable);
  }
  writeBlock("#" + drivingXVariable + "=#590");
  writeBlock("#" + drivingYVariable + "=#591");
  if (transferX) {
    writeBlock("#" + selectedXVariable + "=#592");
  }
  if (transferY) {
    writeBlock("#" + selectedYVariable + "=#593");
  }
  writeMatsuuraProbeDrivingWorkOffset();
  matsuuraProbePendingXYReturnAfterTransfer = true;
}

function isMatsuuraProbePlaneAngleCycle() {
  return (cycleType == "probing-x-plane-angle") || (cycleType == "probing-y-plane-angle");
}

function isMatsuuraFinalPlaneAngleProbeSection() {
  return isMatsuuraProbePlaneAngleCycle() && isLastSection();
}

function validateMatsuuraProbeCycle(cycle) {
  validate(isSameDirection(currentSection.workPlane.forward, new Vector(0, 0, 1)), "Matsuura probing output currently supports only top-plane WCS probing.");
  validate(!printProbeResults(), "Matsuura probing output does not support Fusion print results yet.");
  validate(!cycle.updateToolWear, "Matsuura probing output does not support Fusion tool wear update yet.");
  if (!isMatsuuraProbePlaneAngleCycle()) {
    validate(cycle.angleAskewAction != "stop-message", "Matsuura probing output does not support Fusion angle stop action yet.");
  }
  validate(cycle.wrongSizeAction != "stop-message", "Matsuura probing output does not support Fusion wrong-size stop action yet.");
  validate(cycle.outOfPositionAction != "stop-message", "Matsuura probing output does not support Fusion out-of-position stop action yet.");
  getMatsuuraProbeWorkOffset();
  getMatsuuraProbeDrivingWorkOffset();
  validate(isFinite(cycle.depth) && (cycle.depth > 0), "Matsuura probing requires a positive Fusion probe depth.");
}

function writeMatsuuraProbeStartPosition(x, y, z) {
  var currentPosition = getCurrentPosition();
  if (currentPosition && isFinite(currentPosition.z) && (currentPosition.z < z)) {
    writeBlock(gMotionModal.format(0), zOutput.format(z));
  }
  writeBlock(gMotionModal.format(0), xOutput.format(x), yOutput.format(y));
  writeBlock(gMotionModal.format(0), zOutput.format(z));
  setCurrentPosition(new Vector(x, y, z));
}

function writeMatsuuraProbeMacro(macroNumber, cycle, x, y, z, sizeWords) {
  validateMatsuuraProbeCycle(cycle);
  writeMatsuuraProbeSettings(cycle);
  writeMatsuuraProbeStartPosition(x, y, z);
  writeMatsuuraProbeBeginXYTransferIfNeeded();
  writeBlock(
    gFormat.format(65),
    "P" + macroNumber,
    "A" + xyzFormat.format(getMatsuuraProbeProperty("matsuuraProbeResultNumber", 49)),
    "I" + xyzFormat.format(x),
    "J" + xyzFormat.format(y),
    "K" + xyzFormat.format(-Math.abs(cycle.depth)),
    sizeWords
  );
  writeMatsuuraProbeEndXYTransferIfNeeded();
  setCurrentPosition(new Vector(x, y, z));
}

function writeMatsuuraProbeZMacro(cycle, x, y, z) {
  validateMatsuuraProbeCycle(cycle);
  writeMatsuuraProbeSettings(cycle);
  writeMatsuuraProbeStartPosition(x, y, z);
  var zOffsetVariable = getMatsuuraProbeSelectedZVariable();
  var drivingZVariable = getMatsuuraProbeDrivingZVariable();
  var programmedSurfaceZ = z - cycle.depth;
  var touchedFaceZeroAdjustment = "";
  if (Math.abs(programmedSurfaceZ) > 0.0001) {
    touchedFaceZeroAdjustment = (programmedSurfaceZ > 0 ? "+" : "") + xyzFormat.format(programmedSurfaceZ);
  }
  writeBlock("#590=#5203");
  writeBlock(
    gFormat.format(65),
    "P8300",
    "A" + xyzFormat.format(getMatsuuraProbeProperty("matsuuraProbeResultNumber", 49)),
    "I" + xyzFormat.format(x),
    "J" + xyzFormat.format(y),
    "K" + xyzFormat.format(-Math.abs(cycle.depth))
  );
  writeBlock("#591=#5203-#590");
  writeBlock("#5203=#590");
  if (isMatsuuraProbeDrivingWorkOffsetOverridden()) {
    warning("Matsuura Probe WCS Z-face override: machine will probe under " + formatMatsuuraProbeWorkOffsetName(getMatsuuraProbeDrivingWorkOffset()) + " and update " + formatMatsuuraProbeWorkOffsetName(getMatsuuraProbeWorkOffset()) + ". Fusion X/Y probe point must be authored in the driving/reference WCS frame.");
    writeBlock("#592=#" + drivingZVariable + "+#591" + touchedFaceZeroAdjustment);
    writeBlock("#" + zOffsetVariable + "=#592");
  } else {
    writeBlock("#" + zOffsetVariable + "=#" + zOffsetVariable + "+#591" + touchedFaceZeroAdjustment);
  }
  writeMatsuuraProbeDrivingWorkOffset();
  setCurrentPosition(new Vector(x, y, z));
}

function getMatsuuraProbeP8600Target(target) {
  return Math.abs(target) > 0.0001 ? target : 0.123;
}

function validateMatsuuraProbeP8600DrivingWorkOffset() {
  // The installed O8600 macro uses the 48-set G54.1 base for active-WCS writes.
  validate(getMatsuuraProbeDrivingWorkOffset() <= 54, "Matsuura O8600 edge/corner probing supports driving WCS only through G54.1 P48; use G54-G59 or G54.1 P1-P48 as the driving WCS when updating G54.1 P49-P300.");
}

function writeMatsuuraProbeP8600Axis(axisWord, offsetVariable, target, positiveDirection, feed, approachDistance) {
  var macroTarget = getMatsuuraProbeP8600Target(target);
  validateMatsuuraProbeP8600DrivingWorkOffset();
  writeMatsuuraProbeBeginXYTransferIfNeeded();
  writeBlock(
    gFormat.format(65),
    "P8600",
    axisWord + xyzFormat.format(macroTarget),
    conditional(!positiveDirection, "M-1."),
    "F" + xyzFormat.format(feed),
    "R" + xyzFormat.format(approachDistance)
  );
  forceMatsuuraProbeAbsoluteRapidModals();
  writeBlock(gAbsIncModal.format(90), gMotionModal.format(0));
  writeBlock(mFormat.format(108));
  // O8600 computes an absolute WCS axis value for the touched face.
  // Transfer that measured value to the target WCS, then restore the driving WCS.
  writeMatsuuraProbeEndXYTransferIfNeeded(axisWord == "I", axisWord == "J");
  if (Math.abs(macroTarget - target) > 0.0001) {
    writeBlock("#" + offsetVariable + "=#" + offsetVariable + "+" + xyzFormat.format(macroTarget) + "-" + xyzFormat.format(target));
  }
  matsuuraProbePendingP8600ClearanceBeforeXY = true;
}

function getMatsuuraProbeP8600ApproachDistance(cycle) {
  var approachDistance = Math.max(cycle.probeClearance + cycle.probeOvertravel + getMatsuuraProbeDiameter(), getMatsuuraProbeApproachDistance(cycle) + getMatsuuraProbeDiameter());
  validate(isFinite(cycle.probeClearance) && (cycle.probeClearance > 0), "Matsuura edge probing requires a positive Fusion probe clearance.");
  validate(isFinite(approachDistance) && (approachDistance > getMatsuuraProbeApproachDistance(cycle)), "Matsuura P8600 approach distance must be greater than #504.");
  return approachDistance;
}

function getMatsuuraProbeCAngleSearchDistance(cycle) {
  var searchDistance = Math.max(cycle.probeClearance + cycle.probeOvertravel + getMatsuuraProbeDiameter(), getMatsuuraProbeApproachDistance(cycle) + getMatsuuraProbeDiameter());
  validate(isFinite(cycle.probeClearance) && (cycle.probeClearance > 0), "Matsuura C-angle probing requires a positive Fusion probe clearance.");
  validate(isFinite(cycle.probeOvertravel) && (cycle.probeOvertravel > 0), "Matsuura C-angle probing requires a positive Fusion probe overtravel.");
  validate(isFinite(searchDistance) && (searchDistance > getMatsuuraProbeApproachDistance(cycle)), "Matsuura O1950 search distance must be greater than #504.");
  return searchDistance;
}

function writeMatsuuraProbeCAngleAlignMacro(cycle, x, y, z, axis) {
  validateMatsuuraProbeCycle(cycle);
  validate(!isMatsuuraProbeDrivingWorkOffsetOverridden(), "Matsuura O1950 C-angle probing requires Probe WCS and driving WCS to be the same.");
  validate(isFinite(cycle.probeSpacing) && (cycle.probeSpacing > 0), "Matsuura C-angle probing requires a positive Fusion probe spacing.");
  writeMatsuuraProbeSettings(cycle);

  var direction = approach(cycle.approach1);
  var directionCode = (axis == "X") ? (direction > 0 ? 1 : -1) : (direction > 0 ? 2 : -2);
  var halfSpacing = cycle.probeSpacing / 2;
  var firstX = x;
  var firstY = y;
  var secondX = x;
  var secondY = y;
  if (axis == "X") {
    firstY = y - halfSpacing;
    secondY = y + halfSpacing;
  } else {
    firstX = x - halfSpacing;
    secondX = x + halfSpacing;
  }

  writeMatsuuraProbeStartPosition(firstX, firstY, z);
  writeBlock(
    gFormat.format(65),
    "P1950",
    "A" + xyzFormat.format(getMatsuuraProbeProperty("matsuuraProbeResultNumber", 49)),
    "H" + xyzFormat.format(directionCode),
    "R" + xyzFormat.format(getMatsuuraProbeCAngleSearchDistance(cycle)),
    conditional(cycle.angleAskewAction == "stop-message", "T" + xyzFormat.format(cycle.toleranceAngle ? cycle.toleranceAngle : 0)),
    "I" + xyzFormat.format(firstX),
    "J" + xyzFormat.format(firstY),
    "K" + xyzFormat.format(-Math.abs(cycle.depth)),
    "X" + xyzFormat.format(secondX),
    "Y" + xyzFormat.format(secondY),
    "Z" + xyzFormat.format(-Math.abs(cycle.depth))
  );
  // O1950 retracts to machine Z home before correcting C. Do not let Fusion
  // return to its local retract/start point after the part has rotated.
  matsuuraProbePendingCAngleClearanceBeforeXY = false;
  matsuuraProbeSuppressCAngleReturnRapid = true;
  matsuuraProbeSkipCAngleCycleRetract = true;
  matsuuraProbeForceFullReinitAfterCAngle = true;
}

function writeMatsuuraProbeEdgeMacro(cycle, x, y, z, axis) {
  validateMatsuuraProbeCycle(cycle);
  writeMatsuuraProbeSettings(cycle);
  var probeDiameter = getMatsuuraProbeDiameter();
  var direction = approach(cycle.approach1);
  var measureZ = z - cycle.depth;
  var target = (axis == "X" ? x : y) + direction * (cycle.probeClearance + probeDiameter / 2);
  validate(isFinite(measureZ), "Matsuura edge probing requires a valid measurement Z.");

  writeMatsuuraProbeStartPosition(x, y, z);
  writeBlock(gMotionModal.format(0), zOutput.format(measureZ));
  if (axis == "X") {
    writeMatsuuraProbeP8600Axis("I", getMatsuuraProbeSelectedXVariable(), target, direction > 0, getMatsuuraProbeFastFeed(cycle), getMatsuuraProbeP8600ApproachDistance(cycle));
  } else {
    writeMatsuuraProbeP8600Axis("J", getMatsuuraProbeSelectedYVariable(), target, direction > 0, getMatsuuraProbeFastFeed(cycle), getMatsuuraProbeP8600ApproachDistance(cycle));
  }
  setCurrentPosition(new Vector(x, y, measureZ));
}

function writeMatsuuraProbeWallMacro(cycle, x, y, z, axis) {
  validateMatsuuraProbeCycle(cycle);
  validate(cycle.width1 > 0, "Matsuura wall probing width must be greater than 0.");
  writeMatsuuraProbeSettings(cycle);
  writeMatsuuraProbeStartPosition(x, y, z);
  writeMatsuuraProbeBeginXYTransferIfNeeded();
  writeBlock(
    gFormat.format(65),
    "P8410",
    "A" + xyzFormat.format(getMatsuuraProbeProperty("matsuuraProbeResultNumber", 49)),
    axis == "X" ? "I" + xyzFormat.format(x) : "J" + xyzFormat.format(y),
    "K" + xyzFormat.format(-Math.abs(cycle.depth)),
    axis == "X" ? "E" + xyzFormat.format(cycle.width1) : "F" + xyzFormat.format(cycle.width1)
  );
  writeMatsuuraProbeEndXYTransferIfNeeded(axis == "X", axis == "Y");
  setCurrentPosition(new Vector(x, y, z));
}

function writeMatsuuraProbeChannelMacro(cycle, x, y, z, axis, withIsland) {
  validateMatsuuraProbeCycle(cycle);
  var probeDiameter = getMatsuuraProbeDiameter();
  validate(cycle.width1 > probeDiameter, "Matsuura inside-channel probing width must be larger than the probe diameter.");
  if (withIsland) {
    validate(isFinite(cycle.probeClearance) && (cycle.probeClearance > 0), "Matsuura channel-with-island probing requires a positive Fusion probe clearance.");
    validate(2 * cycle.probeClearance < cycle.width1 - probeDiameter, "Matsuura channel-with-island Fusion clearance must be less than half the channel free width.");
  }
  writeMatsuuraProbeSettings(cycle);
  writeMatsuuraProbeStartPosition(x, y, z);
  writeMatsuuraProbeBeginXYTransferIfNeeded();
  writeBlock(
    gFormat.format(65),
    "P" + (withIsland ? 8420 : 8430),
    "A" + xyzFormat.format(getMatsuuraProbeProperty("matsuuraProbeResultNumber", 49)),
    "I" + xyzFormat.format(x),
    "J" + xyzFormat.format(y),
    "K" + xyzFormat.format(-Math.abs(cycle.depth)),
    axis == "X" ? "E" + xyzFormat.format(cycle.width1) : "F" + xyzFormat.format(cycle.width1),
    withIsland ? "R" + xyzFormat.format(-cycle.probeClearance) : undefined
  );
  writeMatsuuraProbeEndXYTransferIfNeeded(axis == "X", axis == "Y");
  setCurrentPosition(new Vector(x, y, z));
}

function writeMatsuuraProbeOuterCornerMacro(cycle, x, y, z) {
  validateMatsuuraProbeCycle(cycle);
  writeMatsuuraProbeSettings(cycle);
  var probeDiameter = getMatsuuraProbeDiameter();
  var xDirection = approach(cycle.approach1);
  var yDirection = approach(cycle.approach2);
  var targetX = x + xDirection * (cycle.probeClearance + probeDiameter / 2);
  var targetY = y + yDirection * (cycle.probeClearance + probeDiameter / 2);
  var measureZ = z - cycle.depth;
  var xyOffset = cycle.probeOvertravel * 2.5 + probeDiameter;
  var p8600ApproachDistance = Math.max(cycle.probeClearance + cycle.probeOvertravel + probeDiameter, getMatsuuraProbeApproachDistance(cycle) + probeDiameter);
  validate(isFinite(cycle.probeClearance) && (cycle.probeClearance > 0), "Matsuura outer-corner probing requires a positive Fusion probe clearance.");
  validate(isFinite(p8600ApproachDistance) && (p8600ApproachDistance > getMatsuuraProbeApproachDistance(cycle)), "Matsuura P8600 approach distance must be greater than #504.");
  validate(isFinite(measureZ), "Matsuura outer-corner probing requires a valid measurement Z.");

  writeMatsuuraProbeStartPosition(x, y + yDirection * xyOffset, z);
  writeBlock(gMotionModal.format(0), zOutput.format(measureZ));
  writeMatsuuraProbeP8600Axis("I", getMatsuuraProbeSelectedXVariable(), targetX, xDirection > 0, getMatsuuraProbeFastFeed(cycle), p8600ApproachDistance);

  writeMatsuuraProbeFullClearanceXYMove(x + xDirection * xyOffset, y, z);
  writeBlock(gMotionModal.format(0), zOutput.format(measureZ));
  writeMatsuuraProbeP8600Axis("J", getMatsuuraProbeSelectedYVariable(), targetY, yDirection > 0, getMatsuuraProbeFastFeed(cycle), p8600ApproachDistance);
  setCurrentPosition(new Vector(x + xDirection * xyOffset, y, measureZ));
}

function writeMatsuuraProbeCycle(cycle, x, y, z) {
  switch (cycleType) {
  case "probing-x":
    writeMatsuuraProbeEdgeMacro(cycle, x, y, z, "X");
    break;
  case "probing-y":
    writeMatsuuraProbeEdgeMacro(cycle, x, y, z, "Y");
    break;
  case "probing-z":
    writeMatsuuraProbeZMacro(cycle, x, y, z);
    break;
  case "probing-x-wall":
    writeMatsuuraProbeWallMacro(cycle, x, y, z, "X");
    break;
  case "probing-y-wall":
    writeMatsuuraProbeWallMacro(cycle, x, y, z, "Y");
    break;
  case "probing-x-channel":
    writeMatsuuraProbeChannelMacro(cycle, x, y, z, "X", false);
    break;
  case "probing-y-channel":
    writeMatsuuraProbeChannelMacro(cycle, x, y, z, "Y", false);
    break;
  case "probing-x-channel-with-island":
    writeMatsuuraProbeChannelMacro(cycle, x, y, z, "X", true);
    break;
  case "probing-y-channel-with-island":
    writeMatsuuraProbeChannelMacro(cycle, x, y, z, "Y", true);
    break;
  case "probing-x-plane-angle":
    writeMatsuuraProbeCAngleAlignMacro(cycle, x, y, z, "X");
    break;
  case "probing-y-plane-angle":
    writeMatsuuraProbeCAngleAlignMacro(cycle, x, y, z, "Y");
    break;
  case "probing-xy-outer-corner":
    writeMatsuuraProbeOuterCornerMacro(cycle, x, y, z);
    break;
  case "probing-xy-circular-hole":
    validate(cycle.width1 > getMatsuuraProbeDiameter(), "Circular inside probing diameter must be larger than the probe diameter.");
    writeMatsuuraProbeMacro(8200, cycle, x, y, z, "D" + xyzFormat.format(cycle.width1));
    break;
  case "probing-xy-circular-boss":
    validate(cycle.width1 > 0, "Circular outside probing diameter must be greater than 0.");
    writeMatsuuraProbeMacro(8210, cycle, x, y, z, "D" + xyzFormat.format(cycle.width1));
    break;
  case "probing-xy-rectangular-hole":
    validate((cycle.width1 > getMatsuuraProbeDiameter()) && (cycle.width2 > getMatsuuraProbeDiameter()), "Rectangular inside probing sizes must be larger than the probe diameter.");
    writeMatsuuraProbeMacro(8400, cycle, x, y, z, ["E" + xyzFormat.format(cycle.width1), "F" + xyzFormat.format(cycle.width2)]);
    break;
  case "probing-xy-rectangular-boss":
    validate((cycle.width1 > 0) && (cycle.width2 > 0), "Rectangular outside probing sizes must be greater than 0.");
    writeMatsuuraProbeMacro(8410, cycle, x, y, z, ["E" + xyzFormat.format(cycle.width1), "F" + xyzFormat.format(cycle.width2)]);
    break;
  default:
    error(subst("Matsuura probing output does not support Fusion cycle type '%1' yet.", cycleType));
  }
}

function protectedProbeMove(_cycle, x, y, z) {
  var _x = xOutput.format(x);
  var _y = yOutput.format(y);
  var _z = zOutput.format(z);
  if (_z && z >= getCurrentPosition().z) {
    writeBlock(gFormat.format(65), "P" + (probeBaseNumber + 10), _z, getFeed(cycle.feedrate)); // protected positioning move
  }
  if (_x || _y) {
    writeBlock(gFormat.format(65), "P" + (probeBaseNumber + 10), _x, _y, getFeed(highFeedrate)); // protected positioning move
  }
  if (_z && z < getCurrentPosition().z) {
    writeBlock(gFormat.format(65), "P" + (probeBaseNumber + 10), _z, getFeed(cycle.feedrate)); // protected positioning move
  }
}

var probeVariables = {
  outputRotationCodes: false, // determines if it is required to output rotation codes
  compensationXY     : undefined,
  probeAngleMethod   : undefined
};

function writeProbeCycle(cycle, x, y, z) {
  if (isProbeOperation()) {
    if (!settings.workPlaneMethod.useTiltedWorkplane && !isSameDirection(currentSection.workPlane.forward, new Vector(0, 0, 1))) {
      if (!settings.probing.allowIndexingWCSProbing && currentSection.strategy == "probe") {
        error(localize("Updating WCS / work offset using probing is only supported by the CNC in the WCS frame."));
        return;
      }
    }
    var isMirrored = currentSection.getInternalPatternId && currentSection.getInternalPatternId() != currentSection.getPatternId();
    validate(!isMirrored, "Mirror pattern is not supported for Probing toolpaths.");
    if (currentSection.isPatterned && currentSection.isPatterned()) {
      // probe cycles that cannot be used with patterns
      var unsupportedCycleTypes = ["probing-x", "probing-y", "probing-xy-inner-corner", "probing-xy-outer-corner", "probing-x-plane-angle", "probing-y-plane-angle"];
      if (unsupportedCycleTypes.indexOf(cycleType) > -1 && (!Matrix.diff(new Matrix(), currentSection.workPlane).isZero())) {
        error(subst("Rotary type patterns are not supported for the Probing cycle type '%1'.", cycleType));
      }
    }
    if (useMatsuuraProbingMacros()) {
      writeMatsuuraProbeCycle(cycle, x, y, z);
      return;
    }
    if (printProbeResults()) {
      writeProbingToolpathInformation(z - cycle.depth + tool.diameter / 2);
      inspectionWriteCADTransform();
      inspectionWriteWorkplaneTransform();
      if (typeof inspectionWriteVariables == "function") {
        inspectionVariables.pointNumber += 1;
      }
    }
    protectedProbeMove(cycle, x, y, z);
  }

  switch (cycleType) {
  case "probing-x":
    protectedProbeMove(cycle, x, y, z - cycle.depth);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 11),
      "X" + xyzFormat.format(x + approach(cycle.approach1) * (cycle.probeClearance + tool.diameter / 2)),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-y":
    protectedProbeMove(cycle, x, y, z - cycle.depth);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 11),
      "Y" + xyzFormat.format(y + approach(cycle.approach1) * (cycle.probeClearance + tool.diameter / 2)),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-z":
    protectedProbeMove(cycle, x, y, Math.min(z - cycle.depth + cycle.probeClearance, cycle.retract));
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 11),
      "Z" + xyzFormat.format(z - cycle.depth),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-x-wall":
    protectedProbeMove(cycle, x, y, z);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 12),
      "X" + xyzFormat.format(cycle.width1),
      zOutput.format(z - cycle.depth),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "R" + xyzFormat.format(cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-y-wall":
    protectedProbeMove(cycle, x, y, z);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 12),
      "Y" + xyzFormat.format(cycle.width1),
      zOutput.format(z - cycle.depth),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "R" + xyzFormat.format(cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-x-channel":
    protectedProbeMove(cycle, x, y, z - cycle.depth);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 12),
      "X" + xyzFormat.format(cycle.width1),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      // not required "R" + xyzFormat.format(cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-x-channel-with-island":
    protectedProbeMove(cycle, x, y, z);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 12),
      "X" + xyzFormat.format(cycle.width1),
      zOutput.format(z - cycle.depth),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "R" + xyzFormat.format(-cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-y-channel":
    protectedProbeMove(cycle, x, y, z - cycle.depth);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 12),
      "Y" + xyzFormat.format(cycle.width1),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      // not required "R" + xyzFormat.format(cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-y-channel-with-island":
    protectedProbeMove(cycle, x, y, z);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 12),
      "Y" + xyzFormat.format(cycle.width1),
      zOutput.format(z - cycle.depth),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "R" + xyzFormat.format(-cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-xy-circular-boss":
    protectedProbeMove(cycle, x, y, z);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 14),
      "D" + xyzFormat.format(cycle.width1),
      "Z" + xyzFormat.format(z - cycle.depth),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "R" + xyzFormat.format(cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-xy-circular-partial-boss":
    protectedProbeMove(cycle, x, y, z);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 23),
      "A" + xyzFormat.format(cycle.partialCircleAngleA),
      "B" + xyzFormat.format(cycle.partialCircleAngleB),
      "C" + xyzFormat.format(cycle.partialCircleAngleC),
      "D" + xyzFormat.format(cycle.width1),
      "Z" + xyzFormat.format(z - cycle.depth),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "R" + xyzFormat.format(cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-xy-circular-hole":
    protectedProbeMove(cycle, x, y, z - cycle.depth);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 14),
      "D" + xyzFormat.format(cycle.width1),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      // not required "R" + xyzFormat.format(cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-xy-circular-partial-hole":
    protectedProbeMove(cycle, x, y, z - cycle.depth);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 23),
      "A" + xyzFormat.format(cycle.partialCircleAngleA),
      "B" + xyzFormat.format(cycle.partialCircleAngleB),
      "C" + xyzFormat.format(cycle.partialCircleAngleC),
      "D" + xyzFormat.format(cycle.width1),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-xy-circular-hole-with-island":
    protectedProbeMove(cycle, x, y, z);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 14),
      "Z" + xyzFormat.format(z - cycle.depth),
      "D" + xyzFormat.format(cycle.width1),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "R" + xyzFormat.format(-cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-xy-circular-partial-hole-with-island":
    protectedProbeMove(cycle, x, y, z);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 23),
      "Z" + xyzFormat.format(z - cycle.depth),
      "A" + xyzFormat.format(cycle.partialCircleAngleA),
      "B" + xyzFormat.format(cycle.partialCircleAngleB),
      "C" + xyzFormat.format(cycle.partialCircleAngleC),
      "D" + xyzFormat.format(cycle.width1),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "R" + xyzFormat.format(-cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-xy-rectangular-hole":
    protectedProbeMove(cycle, x, y, z - cycle.depth);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 12),
      "X" + xyzFormat.format(cycle.width1),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      // not required "R" + xyzFormat.format(-cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 12),
      "Y" + xyzFormat.format(cycle.width2),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      // not required "R" + xyzFormat.format(-cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-xy-rectangular-boss":
    protectedProbeMove(cycle, x, y, z);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 12),
      "Z" + xyzFormat.format(z - cycle.depth),
      "X" + xyzFormat.format(cycle.width1),
      "R" + xyzFormat.format(cycle.probeClearance),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      getProbingArguments(cycle, true)
    );
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 12),
      "Z" + xyzFormat.format(z - cycle.depth),
      "Y" + xyzFormat.format(cycle.width2),
      "R" + xyzFormat.format(cycle.probeClearance),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-xy-rectangular-hole-with-island":
    protectedProbeMove(cycle, x, y, z);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 12),
      "Z" + xyzFormat.format(z - cycle.depth),
      "X" + xyzFormat.format(cycle.width1),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "R" + xyzFormat.format(-cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 12),
      "Z" + xyzFormat.format(z - cycle.depth),
      "Y" + xyzFormat.format(cycle.width2),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "R" + xyzFormat.format(-cycle.probeClearance),
      getProbingArguments(cycle, true)
    );
    break;

  case "probing-xy-inner-corner":
    var cornerX = x + approach(cycle.approach1) * (cycle.probeClearance + tool.diameter / 2);
    var cornerY = y + approach(cycle.approach2) * (cycle.probeClearance + tool.diameter / 2);
    var cornerI = 0;
    var cornerJ = 0;
    if (cycle.probeSpacing !== undefined) {
      cornerI = cycle.probeSpacing;
      cornerJ = cycle.probeSpacing;
    }
    if ((cornerI != 0) && (cornerJ != 0)) {
      if (currentSection.strategy == "probe") {
        setProbeAngleMethod();
      }
    }
    protectedProbeMove(cycle, x, y, z - cycle.depth);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 15), xOutput.format(cornerX), yOutput.format(cornerY),
      conditional(cornerI != 0, "I" + xyzFormat.format(cornerI)),
      conditional(cornerJ != 0, "J" + xyzFormat.format(cornerJ)),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-xy-outer-corner":
    var cornerX = x + approach(cycle.approach1) * (cycle.probeClearance + tool.diameter / 2);
    var cornerY = y + approach(cycle.approach2) * (cycle.probeClearance + tool.diameter / 2);
    var cornerI = 0;
    var cornerJ = 0;
    if (cycle.probeSpacing !== undefined) {
      cornerI = cycle.probeSpacing;
      cornerJ = cycle.probeSpacing;
    }
    if ((cornerI != 0) && (cornerJ != 0)) {
      if (currentSection.strategy == "probe") {
        setProbeAngleMethod();
      }
    }
    protectedProbeMove(cycle, x, y, z - cycle.depth);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 16), xOutput.format(cornerX), yOutput.format(cornerY),
      conditional(cornerI != 0, "I" + xyzFormat.format(cornerI)),
      conditional(cornerJ != 0, "J" + xyzFormat.format(cornerJ)),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      getProbingArguments(cycle, true)
    );
    break;
  case "probing-x-plane-angle":
    protectedProbeMove(cycle, x, y, z - cycle.depth);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 43),
      "X" + xyzFormat.format(x + approach(cycle.approach1) * (cycle.probeClearance + tool.diameter / 2)),
      "D" + xyzFormat.format(cycle.probeSpacing),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "A" + xyzFormat.format(cycle.nominalAngle != undefined ? cycle.nominalAngle : 90),
      getProbingArguments(cycle, false)
    );
    if (currentSection.strategy == "probe") {
      setProbeAngleMethod();
      probeVariables.compensationXY = "X" + xyzFormat.format(0) + " Y" + xyzFormat.format(0);
    }
    break;
  case "probing-y-plane-angle":
    protectedProbeMove(cycle, x, y, z - cycle.depth);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 43),
      "Y" + xyzFormat.format(y + approach(cycle.approach1) * (cycle.probeClearance + tool.diameter / 2)),
      "D" + xyzFormat.format(cycle.probeSpacing),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "A" + xyzFormat.format(cycle.nominalAngle != undefined ? cycle.nominalAngle : 0),
      getProbingArguments(cycle, false)
    );
    if (currentSection.strategy == "probe") {
      setProbeAngleMethod();
      probeVariables.compensationXY = "X" + xyzFormat.format(0) + " Y" + xyzFormat.format(0);
    }
    break;
  case "probing-xy-pcd-hole":
    protectedProbeMove(cycle, x, y, z);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 19),
      "A" + xyzFormat.format(cycle.pcdStartingAngle),
      "B" + xyzFormat.format(cycle.numberOfSubfeatures),
      "C" + xyzFormat.format(cycle.widthPCD),
      "D" + xyzFormat.format(cycle.widthFeature),
      "K" + xyzFormat.format(z - cycle.depth),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      getProbingArguments(cycle, false)
    );
    if (cycle.updateToolWear) {
      error(localize("Action -Update Tool Wear- is not supported with this cycle."));
      return;
    }
    break;
  case "probing-xy-pcd-boss":
    protectedProbeMove(cycle, x, y, z);
    writeBlock(
      gFormat.format(65), "P" + (probeBaseNumber + 19),
      "A" + xyzFormat.format(cycle.pcdStartingAngle),
      "B" + xyzFormat.format(cycle.numberOfSubfeatures),
      "C" + xyzFormat.format(cycle.widthPCD),
      "D" + xyzFormat.format(cycle.widthFeature),
      "Z" + xyzFormat.format(z - cycle.depth),
      "Q" + xyzFormat.format(cycle.probeOvertravel),
      "R" + xyzFormat.format(cycle.probeClearance),
      getProbingArguments(cycle, false)
    );
    if (cycle.updateToolWear) {
      error(localize("Action -Update Tool Wear- is not supported with this cycle."));
      return;
    }
    break;
  default:
    cycleNotSupported();
  }
}

function printProbeResults() {
  return currentSection.getParameter("printResults", 0) == 1;
}

/** Convert approach to sign. */
function approach(value) {
  validate((value == "positive") || (value == "negative"), "Invalid approach.");
  return (value == "positive") ? 1 : -1;
}

function onCyclePoint(x, y, z) {
  if (isInspectionOperation()) {
    if (typeof inspectionCycleInspect == "function") {
      inspectionCycleInspect(cycle, x, y, z);
      return;
    } else {
      cycleNotSupported();
    }
  } else if (isProbeOperation()) {
    writeProbeCycle(cycle, x, y, z);
  } else {
    writeDrillCycle(cycle, x, y, z);
  }
}

function onCycleEnd() {
  if (isProbeOperation()) {
    zOutput.reset();
    gMotionModal.reset();
    if (useMatsuuraProbingMacros()) {
      if (matsuuraProbeSkipCAngleCycleRetract) {
        matsuuraProbeSkipCAngleCycleRetract = false;
      } else if (!isMatsuuraFinalPlaneAngleProbeSection()) {
        writeBlock(gMotionModal.format(0), zOutput.format(cycle.retract));
        var currentPosition = getCurrentPosition();
        if (currentPosition) {
          setCurrentPosition(new Vector(currentPosition.x, currentPosition.y, cycle.retract));
        }
      }
    } else {
      writeBlock(gFormat.format(65), "P" + (probeBaseNumber + 10), zOutput.format(cycle.retract)); // protected retract move
    }
  } else {
    if (subprogramsAreSupported() && subprogramState.cycleSubprogramIsActive) {
      subprogramEnd();
    }
    if (!cycleExpanded) {
      writeBlock(gFeedModeModal.format(getProperty("useG95") ? 95 : 94), gCycleModal.format(80));
      zOutput.reset();
      gMotionModal.reset();
    }
  }
}

var mapCommand = {
  COMMAND_END                     : 2,
  COMMAND_SPINDLE_CLOCKWISE       : 3,
  COMMAND_SPINDLE_COUNTERCLOCKWISE: 4,
  COMMAND_STOP_SPINDLE            : 5,
  COMMAND_ORIENTATE_SPINDLE       : 19
};

function onCommand(command) {
  switch (command) {
  case COMMAND_COOLANT_OFF:
    setCoolant(COOLANT_OFF);
    return;
  case COMMAND_COOLANT_ON:
    setCoolant(tool.coolant);
    return;
  case COMMAND_STOP:
    writeBlock(mFormat.format(0));
    forceSpindleSpeed = true;
    forceCoolant = true;
    return;
  case COMMAND_OPTIONAL_STOP:
    writeBlock(mFormat.format(1));
    forceSpindleSpeed = true;
    forceCoolant = true;
    return;
  case COMMAND_START_SPINDLE:
    forceSpindleSpeed = false;
    writeBlock(sOutput.format(spindleSpeed), mFormat.format(tool.clockwise ? 3 : 4));
    return;
  case COMMAND_LOAD_TOOL:
    writeToolBlock("T" + toolFormat.format(tool.number), mFormat.format(6));
    writeComment(tool.comment);

    var preloadTool = getNextTool(tool.number != getFirstTool().number);
    if (getProperty("preloadTool") && preloadTool) {
      writeBlock("T" + toolFormat.format(preloadTool.number)); // preload next/first tool
    }
    return;
  case COMMAND_LOCK_MULTI_AXIS:
    var code = parseInt(getProperty("rotaryAxesClampCodes"), 10) == 1 ? 131 : 21;
    writeBlock(rotaryAxisClamp.format(code)); // lock axis
    return;
  case COMMAND_UNLOCK_MULTI_AXIS:
    var code = parseInt(getProperty("rotaryAxesClampCodes"), 10) == 1 ? 132 : 22;
    writeBlock(rotaryAxisClamp.format(code)); // unlock axis
    return;
  case COMMAND_START_CHIP_TRANSPORT:
    return;
  case COMMAND_STOP_CHIP_TRANSPORT:
    return;
  case COMMAND_BREAK_CONTROL:
    return;
  case COMMAND_TOOL_MEASURE:
    return;
  case COMMAND_ACTIVATE_SPEED_FEED_SYNCHRONIZATION:
    return;
  case COMMAND_DEACTIVATE_SPEED_FEED_SYNCHRONIZATION:
    return;
  case COMMAND_PROBE_ON:
    return;
  case COMMAND_PROBE_OFF:
    return;
  }

  var stringId = getCommandStringId(command);
  var mcode = mapCommand[stringId];
  if (mcode != undefined) {
    writeBlock(mFormat.format(mcode));
  } else {
    onUnsupportedCommand(command);
  }
}

function onSectionEnd() {
  if (currentSection.isMultiAxis()) {
    writeBlock(gFeedModeModal.format(getProperty("useG95") ? 95 : 94)); // inverse time feed off
  }
  if (isInspectionOperation() && !isLastSection()) {
    writeBlock(getProperty("commissioningMode") ? onCommand(COMMAND_STOP) : "");
  }
  writeBlock(gPlaneModal.format(17));

  if (!isLastSection()) {
    if (getNextSection().getTool().coolant != tool.coolant) {
      setCoolant(COOLANT_OFF);
    }
    if (tool.breakControl && isToolChangeNeeded(getNextSection(), getProperty("toolAsName") ? "description" : "number")) {
      onCommand(COMMAND_BREAK_CONTROL);
    }
  }

  if (isProbeOperation()) {
    if (useMatsuuraProbingMacros()) {
      var matsuuraProbeContinuation = shouldDeferMatsuuraProbeOffForNextSection();
      if (matsuuraProbeContinuation) {
        matsuuraProbeOnContinuesToNextSection = true;
        matsuuraProbeContinuationMacroFamily = matsuuraProbeContinuation;
      } else {
        matsuuraProbeOnContinuesToNextSection = false;
        matsuuraProbeContinuationMacroFamily = "";
        writeBlock(mFormat.format(109)); // probe off
      }
      matsuuraProbeSuppressCAngleReturnRapid = false;
    } else {
      matsuuraProbeOnContinuesToNextSection = false;
      matsuuraProbeContinuationMacroFamily = "";
      writeBlock(gFormat.format(65), "P" + (probeBaseNumber + 33)); // spin the probe off
    }
    if (probeVariables.probeAngleMethod != "G68") {
      setProbeAngle(); // output probe angle rotations if required
    }
  }
  writeMatsuuraHybridPostCutToolRunEnd();
  if (subprogramsAreSupported() && !matsuuraPalletCfBodyActive) {
    subprogramEnd();
  }
  writeMatsuuraPostCutToolBreakageCheck();
  forceAny();

  operationNeedsSafeStart = false; // reset for next section
}

function onClose() {
  optionalSection = false;
  if (!validateMatsuuraPalletCfApcInspectionClosed()) {
    return;
  }
  validateMatsuuraTailstockClosed();
  if (matsuuraHybridPostCutToolRunActive) {
    error("Hybrid post-cut sister rerun reached program close with an open CF tool-run file.");
  }
  if (isDPRNTopen) {
    writeln("DPRNT[END]");
    writeBlock("PCLOS");
    isDPRNTopen = false;
    if (typeof inspectionProcessSectionEnd == "function") {
      inspectionProcessSectionEnd();
    }
  }
  if (probeVariables.probeAngleMethod == "G68") {
    cancelWCSRotation();
  }

  writeln("");
  onCommand(COMMAND_COOLANT_OFF);
  onCommand(COMMAND_STOP_SPINDLE);
  if (state.tcpIsActive) {
    disableLengthCompensation(true, true); // cancel TCP at clearance before machine-coordinate retract
  }
  // Retract Z to machine home using G53 (safe while G68.2/G43 are active)
  forceModals(gMotionModal, gAbsIncModal);
  writeBlock(gAbsIncModal.format(90), gFormat.format(53), gMotionModal.format(0), "Z" + xyzFormat.format(0));
  state.retractedZ = true; // Z is now at machine home

  if (state.lengthCompensationActive) {
    disableLengthCompensation(true); // G49
  }
  cancelWorkPlane(true); // G69 - cancel G68.2 before changing smoothing modal state
  setSmoothing(false); // G130

  forceWorkPlane();
  writeMatsuuraFinalRotaryCloseout(); // guarded multi-turn reference return or the proven B0/C0 closeout
  if (machineConfiguration.isMultiAxisConfiguration() && currentSection.isMultiAxis()) {
    onCommand(COMMAND_LOCK_MULTI_AXIS);
  }
  matsuuraBClampedForLiveC = false;

  if (probeVariables.probeAngleMethod == "G54.4") {
    writeBlock(gFormat.format(54.4), "P0");
  }

  // Home X/Y using G53
  forceModals(gMotionModal);
  writeBlock(gAbsIncModal.format(90), gFormat.format(53), gMotionModal.format(0), "X" + xyzFormat.format(0), "Y" + xyzFormat.format(0));

  if (matsuuraPalletCfBodyActive) {
    writeln("");
    writeComment("END PALLET CF WORK BODY O" + matsuuraPalletOFormat.format(getMatsuuraPalletCfBodyProgram()));
    writeBlock(mFormat.format(99));
    writeln("%");
    closeRedirection();
    clearMatsuuraPalletCfBodyState();
    return;
  }

  if (!useMatsuuraPalletDataServerScheduleOutput()) {
    writeMatsuuraApcEndExchange();
  }

  writeMatsuuraPalletProgramEnd(); // M30 normally; direct DATA_SV schedule returns to CNC-memory O6597

  if (subprogramsAreSupported()) {
    writeSubprograms();
  }
  writeln("%");
}

// >>>>> INCLUDED FROM include_files/commonFunctions.cpi
// internal variables, do not change
var receivedMachineConfiguration;
var tcp = {isSupportedByControl:getSetting("supportsTCP", true), isSupportedByMachine:false, isSupportedByOperation:false};
var state = {
  retractedX              : false, // specifies that the machine has been retracted in X
  retractedY              : false, // specifies that the machine has been retracted in Y
  retractedZ              : false, // specifies that the machine has been retracted in Z
  tcpIsActive             : false, // specifies that TCP is currently active
  twpIsActive             : false, // specifies that TWP is currently active
  lengthCompensationActive: !getSetting("outputToolLengthCompensation", true), // specifies that tool length compensation is active
  mainState               : true // specifies the current context of the state (true = main, false = optional)
};
var validateLengthCompensation = getSetting("outputToolLengthCompensation", true); // disable validation when outputToolLengthCompensation is disabled
var multiAxisFeedrate;
var sequenceNumber;
var optionalSection = false;
var currentWorkOffset;
var matsuuraRedundantTwpWcsWarningIssued = false;
var matsuuraOutputTwpIsActive = false;
var matsuuraOutputWorkOffset;
var forceSpindleSpeed = false;
var operationNeedsSafeStart = false; // used to convert blocks to optional for safeStartAllOperations
var matsuuraBClampedForLiveC = false;
var matsuuraToolLengthSetTools = {};
var matsuuraToolBreakageCheckedTools = {};
var matsuuraPostCutRerunOperationIndex = 0;
var matsuuraPostCutRerunStartLabel;
var matsuuraPostCutRerunContinueLabel;
var matsuuraPostCutRerunAlarmLabel;
var matsuuraHybridPostCutToolRunIndex = 0;
var matsuuraHybridPostCutToolRunActive = false;
var matsuuraHybridPostCutToolRunProgramNumber;
var matsuuraHybridPostCutToolRunFilePath = "";
var matsuuraPalletCfBodyActive = false;
var matsuuraPalletCfApcInspectionAway = false;
var matsuuraPalletCfApcActionWriting = false;
var matsuuraTailstockPending = false;
var matsuuraTailstockActive = false;
var matsuuraTailstockWasUsed = false;
var matsuuraTailstockDeferredPostCutTool;
var matsuuraTailstockSecondHomeB = toRad(-90);

function validateMatsuuraTailstockActionSettings() {
  if (matsuuraPalletCfBodyActive) {
    error("TAILSTOCK_ON is not supported with Pallet / APC CF work-body output until that combination has a separate machine proof.");
  }
  if (getProperty("matsuuraFinalMultiTurnCReturn", false)) {
    error("TAILSTOCK_ON cannot be combined with Multi-turn C reference return until that B/C reference path has a separate machine proof.");
  }
  if (useMatsuuraPostCutRerunRecovery()) {
    error("TAILSTOCK_ON does not support post-cut sister-tool rerun. A rerun after M122 would require a new guarded M121 engagement sequence.");
  }
}

function validateMatsuuraTailstockSection(_section, insertToolCall) {
  if (!matsuuraTailstockPending && !matsuuraTailstockActive) {
    return;
  }
  validateMatsuuraTailstockActionSettings();
  if (matsuuraTailstockActive && matsuuraTailstockDeferredPostCutTool) {
    error("TAILSTOCK_OFF must immediately follow the operation whose post-cut tool check was deferred. Do not start another operation first.");
  }
  if (_section.isOptional()) {
    error("Tailstock actions cannot span an optional operation because the physical tailstock state would become ambiguous.");
  }
  if (_section.isMultiAxis() || isTCPSupportedByOperation(_section)) {
    error("Tailstock actions currently support indexed G68.2 sections only. Simultaneous/TCP output requires a separate machine proof.");
  }
  if (!useTiltedWorkplaneForIndexedSections()) {
    error("TAILSTOCK_ON requires indexed G68.2 output. Use Workplane output = Automatic or Force indexed G68.2.");
  }
  if (isProbeOperation()) {
    error("TAILSTOCK_ON is not supported for probe operations.");
  }
  var machineABC = getWorkPlaneMachineABC(_section, false);
  if (abcFormat.areDifferent(machineABC.y, matsuuraTailstockSecondHomeB)) {
    error("TAILSTOCK_ON requires the operation machine pose at B-90, matching the proven B-axis second-home tailstock position.");
  }
  if (matsuuraTailstockActive && insertToolCall) {
    error("Insert Manual NC Action TAILSTOCK_OFF before any tool change, then add TAILSTOCK_ON before the next supported B-90 operation.");
  }
}

function writeMatsuuraTailstockCIndex(abc) {
  gMotionModal.reset();
  cOutput.reset();
  var c = cOutput.format(abc.z);
  if (c) {
    writeBlock(gMotionModal.format(0), c);
  }
  setCurrentABC(abc);
  machineSimulation({a:abc.x, b:abc.y, c:abc.z, coordinates:MACHINE});
}

function writeMatsuuraTailstockSecondHomeIndex(abc) {
  onCommand(COMMAND_UNLOCK_MULTI_AXIS);
  forceModals(gAbsIncModal, gMotionModal);
  writeBlock(gAbsIncModal.format(91), gFormat.format(30), "B" + abcFormat.format(0), "P2");
  writeBlock(gAbsIncModal.format(90));
  writeMatsuuraTailstockCIndex(abc);
}

function writeMatsuuraTailstockAdvance() {
  if (!matsuuraTailstockPending) {
    return;
  }
  writeComment("TAILSTOCK ADVANCE - B AXIS AT SECOND HOME");
  writeBlock(mFormat.format(121));
  matsuuraTailstockPending = false;
  matsuuraTailstockActive = true;
}

function writeMatsuuraTailstockRetract() {
  onCommand(COMMAND_COOLANT_OFF);
  onCommand(COMMAND_STOP_SPINDLE);
  forceSpindleSpeed = true;
  forceCoolant = true;
  forceModals(gMotionModal, gAbsIncModal);
  writeBlock(gAbsIncModal.format(90), gFormat.format(53), gMotionModal.format(0), "Z" + xyzFormat.format(0));
  state.retractedZ = true;
  writeComment("TAILSTOCK RETRACT");
  writeBlock(mFormat.format(122));
}

function validateMatsuuraTailstockClosed() {
  if (matsuuraTailstockPending) {
    error("TAILSTOCK_ON was not applied to a supported section. Remove it or place it immediately before an indexed B-90 operation.");
  }
  if (matsuuraTailstockActive) {
    error("Tailstock is still active at program close. Add Manual NC Action TAILSTOCK_OFF before the program end or any tool/B-axis change.");
  }
  if (matsuuraTailstockDeferredPostCutTool) {
    error("A post-cut tool check is still deferred at program close. Add TAILSTOCK_OFF immediately after the supported operation.");
  }
}

function writeRotaryClampMCode(code) {
  var mCode = rotaryAxisClamp.format(code);
  if (mCode) {
    writeBlock(mCode);
  }
}

function clampBAndReleaseCForLiveC() {
  writeRotaryClampMCode(21); // B-axis clamp
  writeRotaryClampMCode(24); // C-axis unclamp
  matsuuraBClampedForLiveC = true;
}

function releaseRotariesForLiveMotion() {
  if (matsuuraBClampedForLiveC) {
    onCommand(COMMAND_UNLOCK_MULTI_AXIS);
    matsuuraBClampedForLiveC = false;
  }
}

function getWorkPlaneOutputMode() {
  var mode = getProperty("useTiltedWorkplane");
  if (mode === true || mode == "true") {
    return "twp";
  } else if (mode === false || mode == "false") {
    return "rotary";
  }
  return mode == undefined ? "auto" : mode;
}

function useTiltedWorkplaneForIndexedSections() {
  var mode = getWorkPlaneOutputMode();
  return mode == "auto" || mode == "twp";
}

function forceTCPForIndexedSections() {
  return getWorkPlaneOutputMode() == "tcp";
}

function useTCPInverseTimeFeed() {
  var mode = getProperty("tcpFeedMode");
  return mode == "g93Seconds" || mode == "g93Minutes";
}

function getTCPInverseTimeUnits() {
  return getProperty("tcpFeedMode") == "g93Seconds" ? INVERSE_SECONDS : INVERSE_MINUTES;
}

function useTWPForMultiAxisTCPPrepositioning() {
  return false; // Matsuura/FANUC: keep G68.2 for indexed 3+2 only, never for TCP cutting sections.
}

function isMatsuuraIndexed3Plus2Section(_section) {
  if (!machineConfiguration.isMultiAxisConfiguration() || _section.isMultiAxis()) {
    return false;
  }
  return getWorkPlaneMachineABC(_section, false).isNonZero();
}

function isCAxisOnlyTCPSection(_section) {
  if (!getProperty("clampBForCAxisTCP") || !_section.isMultiAxis() || !_section.isOptimizedForMachine() || !tcp.isSupportedByOperation) {
    return false;
  }
  var initialABC = _section.getInitialToolAxisABC();
  var finalABC = _section.getFinalToolAxisABC();
  var lowerABC = _section.getLowerToolAxisABC();
  var upperABC = _section.getUpperToolAxisABC();
  var aIsFixed = !abcFormat.areDifferent(lowerABC.x, upperABC.x) && !abcFormat.areDifferent(initialABC.x, finalABC.x);
  var bIsFixed = !abcFormat.areDifferent(lowerABC.y, upperABC.y) && !abcFormat.areDifferent(initialABC.y, finalABC.y);
  var cMoves = abcFormat.areDifferent(lowerABC.z, upperABC.z) || abcFormat.areDifferent(initialABC.z, finalABC.z);
  return aIsFixed && bIsFixed && cMoves;
}

function setRotaryClampForCurrentSection(_section) {
  if (!_section.isMultiAxis()) {
    return;
  }
  if (isCAxisOnlyTCPSection(_section)) {
    // B is clamped after the first B move is made under active TCP.
    releaseRotariesForLiveMotion();
    onCommand(COMMAND_UNLOCK_MULTI_AXIS);
  } else {
    releaseRotariesForLiveMotion();
    onCommand(COMMAND_UNLOCK_MULTI_AXIS);
  }
}

function activateMachine() {
  // disable unsupported rotary axes output
  if (!machineConfiguration.isMachineCoordinate(0) && (typeof aOutput != "undefined")) {
    aOutput.disable();
  }
  if (!machineConfiguration.isMachineCoordinate(1) && (typeof bOutput != "undefined")) {
    bOutput.disable();
  }
  if (!machineConfiguration.isMachineCoordinate(2) && (typeof cOutput != "undefined")) {
    cOutput.disable();
  }

  // setup usage of useTiltedWorkplane
  settings.workPlaneMethod.outputMode = getWorkPlaneOutputMode();
  settings.workPlaneMethod.useTiltedWorkplane = useTiltedWorkplaneForIndexedSections();
  settings.workPlaneMethod.useABCPrepositioning = getSetting("workPlaneMethod.useABCPrepositioning", true);

  if (!machineConfiguration.isMultiAxisConfiguration()) {
    return; // don't need to modify any settings for 3-axis machines
  }

  // identify if any of the rotary axes has TCP enabled
  var axes = [machineConfiguration.getAxisU(), machineConfiguration.getAxisV(), machineConfiguration.getAxisW()];
  tcp.isSupportedByMachine = axes.some(function(axis) {return axis.isEnabled() && axis.isTCPEnabled();}); // true if TCP is enabled on any rotary axis
  if (tcp.isSupportedByMachine) {
    bufferRotaryMoves = false; // disable bufferRotaryMoves if TCP is enabled on any rotary axis
  }

  // save multi-axis feedrate settings from machine configuration
  var mode = machineConfiguration.getMultiAxisFeedrateMode();
  var type = mode == FEED_INVERSE_TIME ? machineConfiguration.getMultiAxisFeedrateInverseTimeUnits() :
    (mode == FEED_DPM ? machineConfiguration.getMultiAxisFeedrateDPMType() : DPM_STANDARD);
  multiAxisFeedrate = {
    mode     : mode,
    maximum  : machineConfiguration.getMultiAxisFeedrateMaximum(),
    type     : type,
    tolerance: mode == FEED_DPM ? machineConfiguration.getMultiAxisFeedrateOutputTolerance() : 0,
    bpwRatio : mode == FEED_DPM ? machineConfiguration.getMultiAxisFeedrateBpwRatio() : 1
  };

  // setup of retract/reconfigure  TAG: Only needed until post kernel supports these machine config settings
  if (receivedMachineConfiguration && machineConfiguration.performRewinds()) {
    safeRetractDistance = machineConfiguration.getSafeRetractDistance();
    safePlungeFeed = machineConfiguration.getSafePlungeFeedrate();
    safeRetractFeed = machineConfiguration.getSafeRetractFeedrate();
  }
  if (typeof safeRetractDistance == "number" && getProperty("safeRetractDistance") != undefined && getProperty("safeRetractDistance") != 0) {
    safeRetractDistance = getProperty("safeRetractDistance");
  }

  if (revision >= 50294) {
    activateAutoPolarMode({tolerance:tolerance / 2, optimizeType:OPTIMIZE_AXIS, expandCycles:getSetting("polarCycleExpandMode", EXPAND_ALL)});
  }

  if (machineConfiguration.isHeadConfiguration() && getSetting("workPlaneMethod.compensateToolLength", false)) {
    for (var i = 0; i < getNumberOfSections(); ++i) {
      var section = getSection(i);
      if (section.isMultiAxis()) {
        machineConfiguration.setToolLength(getBodyLength(section.getTool())); // define the tool length for head adjustments
        section.optimizeMachineAnglesByMachine(machineConfiguration, OPTIMIZE_AXIS);
      }
    }
  } else {
    optimizeMachineAngles2(OPTIMIZE_AXIS);
  }
}

function getBodyLength(tool) {
  for (var i = 0; i < getNumberOfSections(); ++i) {
    var section = getSection(i);
    if (tool.number == section.getTool().number) {
      if (section.hasParameter("operation:tool_assemblyGaugeLength")) { // For Fusion
        return section.getParameter("operation:tool_assemblyGaugeLength", tool.bodyLength + tool.holderLength);
      } else { // Legacy products
        return section.getParameter("operation:tool_overallLength", tool.bodyLength + tool.holderLength);
      }
    }
  }
  return tool.bodyLength + tool.holderLength;
}

function getFeed(f) {
  if (getProperty("useG95")) {
    return feedOutput.format(f / spindleSpeed); // use feed value
  }
  if (typeof activeMovements != "undefined" && activeMovements) {
    var feedContext = activeMovements[movement];
    if (feedContext != undefined) {
      if (!feedFormat.areDifferent(feedContext.feed, f)) {
        if (feedContext.id == currentFeedId) {
          return ""; // nothing has changed
        }
        forceFeed();
        currentFeedId = feedContext.id;
        return settings.parametricFeeds.feedOutputVariable + (settings.parametricFeeds.firstFeedParameter + feedContext.id);
      }
    }
    currentFeedId = undefined; // force parametric feed next time
  }
  return feedOutput.format(f); // use feed value
}

function validateCommonParameters() {
  validateToolData();
  validateMatsuuraCfCardSafeOutputSettings();
  validateMatsuuraApcEndExchangeSettings();
  validateMatsuuraToolManagementOffsetSettings();
  validateMatsuuraToolLengthAutomationSettings();
  for (var i = 0; i < getNumberOfSections(); ++i) {
    var section = getSection(i);
    if (getSection(0).workOffset == 0 && section.workOffset > 0) {
      if (!(typeof wcsDefinitions != "undefined" && wcsDefinitions.useZeroOffset)) {
        error(localize("Using multiple work offsets is not possible if the initial work offset is 0."));
      }
    }
    if (section.isMultiAxis()) {
      if (!section.isOptimizedForMachine() &&
        (!getSetting("workPlaneMethod.useTiltedWorkplane", false) || !getSetting("supportsToolVectorOutput", false))) {
        error(localize("This postprocessor requires a machine configuration for 5-axis simultaneous toolpath."));
      }
      if (machineConfiguration.getMultiAxisFeedrateMode() == FEED_INVERSE_TIME && !getSetting("supportsInverseTimeFeed", true)) {
        error(localize("This postprocessor does not support inverse time feedrates."));
      }
      if (getSetting("supportsToolVectorOutput", false) && !tcp.isSupportedByControl) {
        error(localize("Incompatible postprocessor settings detected." + EOL +
        "Setting 'supportsToolVectorOutput' requires setting 'supportsTCP' to be enabled as well."));
      }
    } else if (!useTiltedWorkplaneForIndexedSections() && !forceTCPForIndexedSections() && isMatsuuraIndexed3Plus2Section(section)) {
      error(subst(
        localize("Indexed 3+2 operation '%1' requires Workplane output set to Automatic, Force TCP G43.4, or Force indexed G68.2. TCP 4/5-axis sections will still output G43.4 without G68.2."),
        section.getParameter("operation-comment", "unnamed")
      ));
    } else if (forceTCPForIndexedSections() && isMatsuuraIndexed3Plus2Section(section) && !tcp.isSupportedByControl) {
      error(subst(
        localize("Indexed 3+2 operation '%1' cannot use Force TCP G43.4 because TCP support is disabled."),
        section.getParameter("operation-comment", "unnamed")
      ));
    }
  }
  if (!tcp.isSupportedByControl && tcp.isSupportedByMachine) {
    error(localize("The machine configuration has TCP enabled which is not supported by this postprocessor."));
  }
  if (getProperty("tcpFeedMode") != "g94") {
    error(localize("G93 inverse-time TCP feed is disabled for this machine because the real-machine 2018 test alarmed 010 IMPROPER G-CODE. Use G94 feed/min."));
  }
  var rotaryLimiterFeed = parseFloat(getProperty("tcpRotaryLimiterFeed"));
  if (isFinite(rotaryLimiterFeed) && rotaryLimiterFeed > 0) {
    warning(localize("Legacy TCP rotary fixed feed limiter is enabled. Air cut before cutting material."));
  }
  if (getProperty("safePositionMethod") == "clearanceHeight") {
    var msg = "-Attention- Property 'Safe Retracts' is set to 'Clearance Height'." + EOL +
      "Ensure the clearance height will clear the part and or fixtures." + EOL +
      "Raise the Z-axis to a safe height before starting the program.";
    warning(msg);
    writeComment(msg);
  }
}

function validateToolData() {
  var _default = 99999;
  var _maximumSpindleRPM = machineConfiguration.getMaximumSpindleSpeed() > 0 ? machineConfiguration.getMaximumSpindleSpeed() :
    settings.maximumSpindleRPM == undefined ? _default : settings.maximumSpindleRPM;
  var _maximumToolNumber = settings.maximumToolNumber != undefined ? settings.maximumToolNumber :
    machineConfiguration.isReceived() && machineConfiguration.getNumberOfTools() > 0 ? machineConfiguration.getNumberOfTools() : _default;
  var _maximumToolLengthOffset = settings.maximumToolLengthOffset == undefined ? _default : settings.maximumToolLengthOffset;
  var _maximumToolDiameterOffset = settings.maximumToolDiameterOffset == undefined ? _default : settings.maximumToolDiameterOffset;

  var header = ["Detected maximum values are out of range.", "Maximum values:"];
  var warnings = {
    toolNumber    : {msg:"Tool number value exceeds the maximum value for tool: " + EOL, max:" Tool number: " + _maximumToolNumber, values:[]},
    lengthOffset  : {msg:"Tool length offset value exceeds the maximum value for tool: " + EOL, max:" Tool length offset: " + _maximumToolLengthOffset, values:[]},
    diameterOffset: {msg:"Tool diameter offset value exceeds the maximum value for tool: " + EOL, max:" Tool diameter offset: " + _maximumToolDiameterOffset, values:[]},
    spindleSpeed  : {msg:"Spindle speed exceeds the maximum value for operation: " + EOL, max:" Spindle speed: " + _maximumSpindleRPM, values:[]}
  };

  var toolIds = [];
  for (var i = 0; i < getNumberOfSections(); ++i) {
    var section = getSection(i);
    if (toolIds.indexOf(section.getTool().getToolId()) === -1) { // loops only through sections which have a different tool ID
      var toolNumber = section.getTool().number;
      var lengthOffset = section.getTool().lengthOffset;
      var diameterOffset = section.getTool().diameterOffset;
      var comment = section.getParameter("operation-comment", "");

      if (toolNumber > _maximumToolNumber && !getProperty("toolAsName")) {
        warnings.toolNumber.values.push(SP + toolNumber + EOL);
      }
      if (lengthOffset > _maximumToolLengthOffset) {
        warnings.lengthOffset.values.push(SP + "Tool " + toolNumber + " (" + comment + "," + " Length offset: " + lengthOffset + ")" + EOL);
      }
      if (diameterOffset > _maximumToolDiameterOffset) {
        warnings.diameterOffset.values.push(SP + "Tool " + toolNumber + " (" + comment + "," + " Diameter offset: " + diameterOffset + ")" + EOL);
      }
      toolIds.push(section.getTool().getToolId());
    }
    // loop through all sections regardless of tool id for idenitfying spindle speeds

    // identify if movement ramp is used in current toolpath, use ramp spindle speed for comparisons
    var ramp = section.getMovements() & ((1 << MOVEMENT_RAMP) | (1 << MOVEMENT_RAMP_ZIG_ZAG) | (1 << MOVEMENT_RAMP_PROFILE) | (1 << MOVEMENT_RAMP_HELIX));
    var _sectionSpindleSpeed = Math.max(section.getTool().spindleRPM, ramp ? section.getTool().rampingSpindleRPM : 0, 0);
    if (_sectionSpindleSpeed > _maximumSpindleRPM) {
      warnings.spindleSpeed.values.push(SP + section.getParameter("operation-comment", "") + " (" + _sectionSpindleSpeed + " RPM" + ")" + EOL);
    }
  }

  // sort lists by tool number
  warnings.toolNumber.values.sort(function(a, b) {return a - b;});
  warnings.lengthOffset.values.sort(function(a, b) {return a.localeCompare(b);});
  warnings.diameterOffset.values.sort(function(a, b) {return a.localeCompare(b);});

  var warningMessages = [];
  for (var key in warnings) {
    if (warnings[key].values != "") {
      header.push(warnings[key].max); // add affected max values to the header
      warningMessages.push(warnings[key].msg + warnings[key].values.join(""));
    }
  }
  if (warningMessages.length != 0) {
    warningMessages.unshift(header.join(EOL) + EOL);
    warning(warningMessages.join(EOL));
  }
}

function forceFeed() {
  currentFeedId = undefined;
  feedOutput.reset();
}

/** Force output of X, Y, and Z. */
function forceXYZ() {
  xOutput.reset();
  yOutput.reset();
  zOutput.reset();
}

/** Force output of A, B, and C. */
function forceABC() {
  aOutput.reset();
  bOutput.reset();
  cOutput.reset();
}

/** Force output of X, Y, Z, A, B, C, and F on next output. */
function forceAny() {
  forceXYZ();
  forceABC();
  forceFeed();
}

/**
  Writes the specified block.
*/
function writeBlock() {
  var text = formatWords(arguments);
  if (!text) {
    return;
  }
  if (!guardMatsuuraOutputBlock(text)) {
    return;
  }
  var prefix = getSetting("sequenceNumberPrefix", "N");
  var suffix = getSetting("writeBlockSuffix", "");
  if ((optionalSection || skipBlocks) && !getSetting("supportsOptionalBlocks", true)) {
    error(localize("Optional blocks are not supported by this post."));
  }
  if (getProperty("showSequenceNumbers") == "true") {
    if (sequenceNumber == undefined || sequenceNumber >= settings.maximumSequenceNumber) {
      sequenceNumber = getProperty("sequenceNumberStart");
    }
    if (optionalSection || skipBlocks) {
      writeWords2("/", prefix + sequenceNumber, text + suffix);
    } else {
      writeWords2(prefix + sequenceNumber, text + suffix);
    }
    sequenceNumber += getProperty("sequenceNumberIncrement");
  } else {
    if (optionalSection || skipBlocks) {
      writeWords2("/", text + suffix);
    } else {
      writeWords(text + suffix);
    }
  }
}

validate(settings.comments, "Setting 'comments' is required but not defined.");
function formatComment(text) {
  var prefix = settings.comments.prefix;
  var suffix = settings.comments.suffix;
  var _permittedCommentChars = settings.comments.permittedCommentChars == undefined ? "" : settings.comments.permittedCommentChars;
  switch (settings.comments.outputFormat) {
  case "upperCase":
    text = text.toUpperCase();
    _permittedCommentChars = _permittedCommentChars.toUpperCase();
    break;
  case "lowerCase":
    text = text.toLowerCase();
    _permittedCommentChars = _permittedCommentChars.toLowerCase();
    break;
  case "ignoreCase":
    _permittedCommentChars = _permittedCommentChars.toUpperCase() + _permittedCommentChars.toLowerCase();
    break;
  default:
    error(localize("Unsupported option specified for setting 'comments.outputFormat'."));
  }
  if (_permittedCommentChars != "") {
    text = filterText(String(text), _permittedCommentChars);
  }
  text = String(text).substring(0, settings.comments.maximumLineLength - prefix.length - suffix.length);
  return text != "" ? prefix + text + suffix : "";
}

/**
  Output a comment.
*/
function writeComment(text) {
  if (!text) {
    return;
  }
  var comments = String(text).split(/\r?\n/);
  for (comment in comments) {
    var _comment = formatComment(comments[comment]);
    if (_comment) {
      if (getSetting("comments.showSequenceNumbers", false)) {
        writeBlock(_comment);
      } else {
        writeln(_comment);
      }
    }
  }
}

function onComment(text) {
  writeComment(text);
}

/**
  Writes the specified block - used for tool changes only.
*/
function writeToolBlock() {
  var show = getProperty("showSequenceNumbers");
  setProperty("showSequenceNumbers", (show == "true" || show == "toolChange") ? "true" : "false");
  writeBlock(arguments);
  setProperty("showSequenceNumbers", show);
  machineSimulation({/*x:toPreciseUnit(200, MM), y:toPreciseUnit(200, MM), coordinates:MACHINE,*/ mode:TOOLCHANGE}); // move machineSimulation to a tool change position
}

var skipBlocks = false;
var initialState = JSON.parse(JSON.stringify(state)); // save initial state
var optionalState = JSON.parse(JSON.stringify(state));
var saveCurrentSectionId = undefined;
function writeStartBlocks(isRequired, code) {
  var saveSkipBlocks = skipBlocks;
  var saveMainState = state; // save main state

  if (!isRequired) {
    if (!getProperty("safeStartAllOperations", false)) {
      return; // when safeStartAllOperations is disabled, dont output code and return
    }
    if (saveCurrentSectionId != getCurrentSectionId()) {
      saveCurrentSectionId = getCurrentSectionId();
      forceModals(); // force all modal variables when entering a new section
      optionalState = Object.create(initialState); // reset optionalState to initialState when entering a new section
    }
    skipBlocks = true; // if values are not required, but safeStartAllOperations is enabled - write following blocks as optional
    state = optionalState; // set state to optionalState if skipBlocks is true
    state.mainState = false;
  }
  code(); // writes out the code which is passed to this function as an argument

  state = saveMainState; // restore main state
  skipBlocks = saveSkipBlocks; // restore skipBlocks value
}

var pendingRadiusCompensation = -1;
function onRadiusCompensation() {
  pendingRadiusCompensation = radiusCompensation;
  if (pendingRadiusCompensation >= 0 && !getSetting("supportsRadiusCompensation", true)) {
    error(localize("Radius compensation mode is not supported."));
    return;
  }
}

function getMatsuuraPassThroughWorkOffset(text) {
  var executable = String(text)
    .replace(/\([^)]*\)/g, "")
    .replace(/^\s*N\d+\s*/i, "")
    .replace(/\s*;\s*$/, "")
    .replace(/^\s+|\s+$/g, "");
  var standard = executable.match(/^G(5[4-9])(?:\.0+)?$/i);
  if (standard) {
    return {word:"G" + standard[1], offset:Number(standard[1]) - 53, isPure:true};
  }
  var extended = executable.match(/^G54\.1\s*P\s*(\d+)$/i);
  if (extended) {
    var extendedNumber = Number(extended[1]);
    return {word:"G54.1 P" + extendedNumber, offset:6 + extendedNumber, isPure:true, isValid:(extendedNumber >= 1) && (extendedNumber <= 300)};
  }
  var dynamicExtended = executable.match(/^G54\.1\s*P\s*(#\d+|\[[^\]]+\])$/i);
  if (dynamicExtended) {
    return {word:"G54.1 P" + dynamicExtended[1], offset:undefined, isPure:true, isValid:true};
  }
  var invalidExtended = executable.match(/^G54\.1\s*P\s*(.+)$/i);
  if (invalidExtended) {
    return {word:"G54.1 P" + invalidExtended[1], offset:undefined, isPure:true, isValid:false};
  }
  if (/^G54\.1$/i.test(executable)) {
    return {word:"G54.1", offset:undefined, isPure:true, isValid:false};
  }
  var contained = executable.match(/G54\.1(?![\d.])|G5[4-9](?![\d.])/i);
  if (contained) {
    return {word:contained[0].toUpperCase(), offset:undefined, isPure:false};
  }
  return undefined;
}

function guardMatsuuraOutputBlock(text) {
  if (!guardMatsuuraPalletCfApcInspectionOutputBlock(text)) {
    return false;
  }
  if (!guardMatsuuraTailstockOutputBlock(text)) {
    return false;
  }
  var executable = String(text).replace(/\([^)]*\)/g, "");
  var activatesTwp = /G68\.2(?![\d.])/i.test(executable);
  var cancelsTwp = /G69(?![\d.])/i.test(executable);
  var workOffset = getMatsuuraPassThroughWorkOffset(text);
  var twpAtBlockEntry = matsuuraOutputTwpIsActive;

  if (workOffset && (workOffset.isValid === false)) {
    error(workOffset.word + " is invalid. This post supports G54.1 P1 through P300.");
    return false;
  }
  if (workOffset && (twpAtBlockEntry || activatesTwp)) {
    if (!activatesTwp && workOffset.isPure && (workOffset.offset != undefined) && (workOffset.offset == matsuuraOutputWorkOffset)) {
      if (!matsuuraRedundantTwpWcsWarningIssued) {
        warning("Ignored redundant " + workOffset.word + " output while G68.2 TWP is active. The post kept the already active work offset and tilted frame.");
        matsuuraRedundantTwpWcsWarningIssued = true;
      }
      return false;
    }
    error(workOffset.word + " cannot be output while G68.2 TWP is active or in the same block as G68.2. Cancel tool length compensation and TWP with G49 then G69 before selecting a work offset.");
    return false;
  }

  if (workOffset) {
    matsuuraOutputWorkOffset = workOffset.isPure ? workOffset.offset : undefined;
  }
  if (activatesTwp) {
    matsuuraOutputTwpIsActive = true;
  }
  if (cancelsTwp) {
    matsuuraOutputTwpIsActive = false;
  }
  return true;
}

function guardMatsuuraPalletCfApcInspectionOutputBlock(text) {
  if (!matsuuraPalletCfApcInspectionAway || matsuuraPalletCfApcActionWriting) {
    return true;
  }
  var executable = String(text).replace(/\([^)]*\)/g, "").replace(/^\s+|\s+$/g, "");
  if (!executable || /^M0*(?:0|1)$/i.test(executable)) {
    return true;
  }
  error("The Pallet CF body's original pallet is away for inspection. Only M00/M01 or the matching APC_EXCHANGE return Action may be output before machining resumes.");
  return false;
}

function guardMatsuuraTailstockOutputBlock(text) {
  if (!matsuuraTailstockActive) {
    return true;
  }
  var executable = String(text).replace(/\([^)]*\)/g, "");
  if (/B\s*(?:[-+]?(?:\d|\.)|#|\[)/i.test(executable)) {
    error("B-axis output is forbidden while the tailstock is active. Output TAILSTOCK_OFF before any B-axis command.");
    return false;
  }
  if (/(^|[^0-9.])M0*6(?!\d)/i.test(executable)) {
    error("Tool change M6 is forbidden while the tailstock is active. Output TAILSTOCK_OFF before changing tools.");
    return false;
  }
  if (/(^|[^0-9.])M0*(?:22|132)(?!\d)/i.test(executable)) {
    error("B-axis unclamp is forbidden while the tailstock is active. Only guarded C-axis release/indexing is allowed.");
    return false;
  }
  if (/G43\.4(?![\d.])/i.test(executable)) {
    error("G43.4 TCP is not supported while the tailstock is active. Use the guarded indexed G68.2 tailstock workflow.");
    return false;
  }
  var tailstockToolMacro = executable.match(/G65(?![\d.])[^\r\n]*P(?:1938|1939|1940|9301|9303)(?!\d)/i);
  if (tailstockToolMacro) {
    error("Tool-setter and tool-breakage macros are forbidden while the tailstock is active. Output M122 before the macro call.");
    return false;
  }
  return true;
}

function onParameter(name, value) {
  if (name != "action") {
    return;
  }
  var action = String(value).replace(/^\s+|\s+$/g, "").toUpperCase();
  if (action == "APC_EXCHANGE") {
    writeMatsuuraApcExchangeAction();
    return;
  }
  if (/^APC/.test(action)) {
    error("Unsupported APC Action '" + value + "'. Use APC_EXCHANGE.");
    return;
  }
  if (action == "TAILSTOCK_ON") {
    validateMatsuuraTailstockActionSettings();
    if (matsuuraTailstockPending || matsuuraTailstockActive) {
      error("TAILSTOCK_ON is already pending or active. Use one matched TAILSTOCK_ON / TAILSTOCK_OFF pair.");
      return;
    }
    matsuuraTailstockWasUsed = true;
    matsuuraTailstockPending = true;
    writeComment("TAILSTOCK ON REQUEST - APPLY AT NEXT SAFE B-90 SECTION");
    return;
  }
  if (action == "TAILSTOCK_OFF") {
    if (matsuuraTailstockPending || !matsuuraTailstockActive) {
      error("TAILSTOCK_OFF has no matching active TAILSTOCK_ON section.");
      return;
    }
    writeMatsuuraTailstockRetract();
    matsuuraTailstockPending = false;
    matsuuraTailstockActive = false;
    writeMatsuuraDeferredTailstockPostCutToolBreakageCheck();
    return;
  }
  if (/^TAILSTOCK/.test(action)) {
    error("Unsupported tailstock Action '" + value + "'. Use TAILSTOCK_ON or TAILSTOCK_OFF.");
  }
}

function onPassThrough(text) {
  var commands = String(text).split(",");
  for (text in commands) {
    var command = commands[text];
    var executable = String(command).replace(/\([^)]*\)/g, "");
    if (/(^|[^0-9.])M0*61(?!\d)/i.test(executable)) {
      error("Manual NC/Pass Through raw M61 is not supported because it bypasses APC positioning and post-state recovery. Use Manual NC Action APC_EXCHANGE.");
      return;
    }
    if (/(^|[^0-9.])M0*12[12](?!\d)/i.test(executable)) {
      error("Manual NC/Pass Through raw M121/M122 is not supported because it bypasses tailstock safety tracking. Use Manual NC Action TAILSTOCK_ON or TAILSTOCK_OFF.");
      return;
    }
    if (/G68\.2(?![\d.])|G69(?![\d.])/i.test(executable)) {
      error("Manual NC/Pass Through raw G68.2/G69 is not supported because it bypasses the post TWP state. Author the tilted workplane in Fusion CAM.");
      return;
    }
    var workOffset = getMatsuuraPassThroughWorkOffset(command);
    if (workOffset && (workOffset.isValid === false)) {
      error("Manual NC/Pass Through " + workOffset.word + " is invalid. This post supports G54.1 P1 through P300.");
      return;
    }
    var rotationCurrent = (typeof gRotationModal != "undefined") ? gRotationModal.getCurrent() : undefined;
    var twpIsActive = matsuuraOutputTwpIsActive || state.twpIsActive || ((rotationCurrent != undefined) && (rotationCurrent != 69));
    var activeWorkOffset = matsuuraOutputTwpIsActive ? matsuuraOutputWorkOffset : currentWorkOffset;
    if (workOffset && twpIsActive) {
      if (workOffset.isPure && (workOffset.offset != undefined) && (workOffset.offset == activeWorkOffset)) {
        if (!matsuuraRedundantTwpWcsWarningIssued) {
          warning("Ignored redundant Manual NC/Pass Through " + workOffset.word + " while G68.2 TWP is active. Remove the redundant WCS command from Fusion; the post kept the already active work offset and tilted frame.");
          matsuuraRedundantTwpWcsWarningIssued = true;
        }
        continue;
      }
      error("Manual NC/Pass Through " + workOffset.word + " cannot be output while G68.2 TWP is active. Cancel the tilted section in CAM or remove/reposition the WCS command; the post will not guess a G49/G69 transition.");
      return;
    }
    writeBlock(command);
    if (workOffset) {
      currentWorkOffset = workOffset.isPure ? workOffset.offset : undefined;
    }
  }
}

function forceModals() {
  if (arguments.length == 0) { // reset all modal variables listed below
    var modals = [
      "gMotionModal",
      "gPlaneModal",
      "gAbsIncModal",
      "gFeedModeModal",
      "feedOutput"
    ];
    if (operationNeedsSafeStart && (typeof currentSection != "undefined" && currentSection.isMultiAxis())) {
      modals.push("fourthAxisClamp", "fifthAxisClamp", "sixthAxisClamp");
    }
    for (var i = 0; i < modals.length; ++i) {
      if (typeof this[modals[i]] != "undefined") {
        this[modals[i]].reset();
      }
    }
  } else {
    for (var i in arguments) {
      arguments[i].reset(); // only reset the modal variable passed to this function
    }
  }
}

/** Helper function to be able to use a default value for settings which do not exist. */
function getSetting(setting, defaultValue) {
  var result = defaultValue;
  var keys = setting.split(".");
  var obj = settings;
  for (var i in keys) {
    if (obj[keys[i]] != undefined) { // setting does exist
      result = obj[keys[i]];
      if (typeof [keys[i]] === "object") {
        obj = obj[keys[i]];
        continue;
      }
    } else { // setting does not exist, use default value
      if (defaultValue != undefined) {
        result = defaultValue;
      } else {
        error("Setting '" + keys[i] + "' has no default value and/or does not exist.");
        return undefined;
      }
    }
  }
  return result;
}

function getForwardDirection(_section) {
  var forward = undefined;
  var _optimizeType = settings.workPlaneMethod && settings.workPlaneMethod.optimizeType;
  if (_section.isMultiAxis()) {
    forward = _section.workPlane.forward;
  } else if (!getSetting("workPlaneMethod.useTiltedWorkplane", false) && machineConfiguration.isMultiAxisConfiguration()) {
    if (_optimizeType == undefined) {
      var saveRotation = getRotation();
      getWorkPlaneMachineABC(_section, true);
      forward = getRotation().forward;
      setRotation(saveRotation); // reset rotation
    } else {
      var abc = getWorkPlaneMachineABC(_section, false);
      var forceAdjustment = settings.workPlaneMethod.optimizeType == OPTIMIZE_TABLES || settings.workPlaneMethod.optimizeType == OPTIMIZE_BOTH;
      forward = machineConfiguration.getOptimizedDirection(_section.workPlane.forward, abc, false, forceAdjustment);
    }
  } else {
    forward = getRotation().forward;
  }
  return forward;
}

function getRetractParameters() {
  var _arguments = typeof arguments[0] === "object" ? arguments[0].axes : arguments;
  var singleLine = arguments[0].singleLine == undefined ? true : arguments[0].singleLine;
  var words = []; // store all retracted axes in an array
  var retractAxes = new Array(false, false, false);
  var method = getProperty("safePositionMethod", "undefined");
  if (method == "clearanceHeight") {
    if (!is3D()) {
      error(localize("Safe retract option 'Clearance Height' is only supported when all operations are along the setup Z-axis."));
    }
    return undefined;
  }
  validate(settings.retract, "Setting 'retract' is required but not defined.");
  validate(_arguments.length != 0, "No axis specified for getRetractParameters().");
  for (i in _arguments) {
    retractAxes[_arguments[i]] = true;
  }
  if ((retractAxes[0] || retractAxes[1]) && !state.retractedZ) { // retract Z first before moving to X/Y home
    error(localize("Retracting in X/Y is not possible without being retracted in Z."));
    return undefined;
  }
  // special conditions
  if (retractAxes[0] || retractAxes[1]) {
    method = getSetting("retract.methodXY", method);
  }
  if (retractAxes[2]) {
    method = getSetting("retract.methodZ", method);
  }
  // define home positions
  var useZeroValues = (settings.retract.useZeroValues && settings.retract.useZeroValues.indexOf(method) != -1);
  var _xHome = machineConfiguration.hasHomePositionX() && !useZeroValues ? machineConfiguration.getHomePositionX() : toPreciseUnit(0, MM);
  var _yHome = machineConfiguration.hasHomePositionY() && !useZeroValues ? machineConfiguration.getHomePositionY() : toPreciseUnit(0, MM);
  var _zHome = machineConfiguration.getRetractPlane() != 0 && !useZeroValues ? machineConfiguration.getRetractPlane() : toPreciseUnit(0, MM);
  for (var i = 0; i < _arguments.length; ++i) {
    switch (_arguments[i]) {
    case X:
      if (!state.retractedX) {
        words.push("X" + xyzFormat.format(_xHome));
        xOutput.reset();
        state.retractedX = true;
      }
      break;
    case Y:
      if (!state.retractedY) {
        words.push("Y" + xyzFormat.format(_yHome));
        yOutput.reset();
        state.retractedY = true;
      }
      break;
    case Z:
      if (!state.retractedZ) {
        words.push("Z" + xyzFormat.format(_zHome));
        zOutput.reset();
        state.retractedZ = true;
      }
      break;
    default:
      error(localize("Unsupported axis specified for getRetractParameters()."));
      return undefined;
    }
  }
  return {
    method     : method,
    retractAxes: retractAxes,
    words      : words,
    positions  : {
      x: retractAxes[0] ? _xHome : undefined,
      y: retractAxes[1] ? _yHome : undefined,
      z: retractAxes[2] ? _zHome : undefined},
    singleLine: singleLine};
}

/** Returns true when subprogram logic does exist into the post. */
function subprogramsAreSupported() {
  return typeof subprogramState != "undefined";
}

// Start of machine simulation connection move support
var debugSimulation = false; // enable to output debug information for connection move support in the NC program
var TCPON = "TCP ON";
var TCPOFF = "TCP OFF";
var TWPON = "TWP ON";
var TWPOFF = "TWP OFF";
var TOOLCHANGE = "TOOL CHANGE";
var RETRACTTOOLAXIS = "RETRACT TOOLAXIS";
var WORK = "WORK CS";
var MACHINE = "MACHINE CS";
var MIN = "MIN";
var MAX = "MAX";
var WARNING_NON_RANGE = [0, 1, 2];
var isTwpOn;
var isTcpOn;
/**
 * Helper function for connection moves in machine simulation.
 * @param {Object} parameters An object containing the desired options for machine simulation.
 * @note Available properties are:
 * @param {Number} x X axis position, alternatively use MIN or MAX to move to the axis limit
 * @param {Number} y Y axis position, alternatively use MIN or MAX to move to the axis limit
 * @param {Number} z Z axis position, alternatively use MIN or MAX to move to the axis limit
 * @param {Number} a A axis position (in radians)
 * @param {Number} b B axis position (in radians)
 * @param {Number} c C axis position (in radians)
 * @param {Number} feed desired feedrate, automatically set to high/current feedrate if not specified
 * @param {String} mode mode TCPON | TCPOFF | TWPON | TWPOFF | TOOLCHANGE | RETRACTTOOLAXIS
 * @param {String} coordinates WORK | MACHINE - if undefined, work coordinates will be used by default
 * @param {Number} eulerAngles the calculated Euler angles for the workplane
 * @example
  machineSimulation({a:abc.x, b:abc.y, c:abc.z, coordinates:MACHINE});
  machineSimulation({x:toPreciseUnit(200, MM), y:toPreciseUnit(200, MM), coordinates:MACHINE, mode:TOOLCHANGE});
*/
function machineSimulation(parameters) {
  if (revision < 50198 || skipBlocks || (getSimulationStreamPath() == "" && !debugSimulation)) {
    return; // return when post kernel revision is lower than 50198 or when skipBlocks is enabled
  }
  getAxisLimit = function(axis, limit) {
    validate(limit == MIN || limit == MAX, subst(localize("Invalid argument \"%1\" passed to the machineSimulation function."), limit));
    var range = axis.getRange();
    if (range.isNonRange()) {
      var axisLetters = ["X", "Y", "Z"];
      var warningMessage = subst(localize("An attempt was made to move the \"%1\" axis to its MIN/MAX limits during machine simulation, but its range is set to \"unlimited\"." + EOL +
        "A limited range must be set for the \"%1\" axis in the machine definition, or these motions will not be shown in machine simulation."), axisLetters[axis.getCoordinate()]);
      warningOnce(warningMessage, WARNING_NON_RANGE[axis.getCoordinate()]);
      return undefined;
    }
    return limit == MIN ? range.minimum : range.maximum;
  };
  var x = (isNaN(parameters.x) && parameters.x) ? getAxisLimit(machineConfiguration.getAxisX(), parameters.x) : parameters.x;
  var y = (isNaN(parameters.y) && parameters.y) ? getAxisLimit(machineConfiguration.getAxisY(), parameters.y) : parameters.y;
  var z = (isNaN(parameters.z) && parameters.z) ? getAxisLimit(machineConfiguration.getAxisZ(), parameters.z) : parameters.z;
  var rotaryAxesErrorMessage = localize("Invalid argument for rotary axes passed to the machineSimulation function. Only numerical values are supported.");
  var a = (isNaN(parameters.a) && parameters.a) ? error(rotaryAxesErrorMessage) : parameters.a;
  var b = (isNaN(parameters.b) && parameters.b) ? error(rotaryAxesErrorMessage) : parameters.b;
  var c = (isNaN(parameters.c) && parameters.c) ? error(rotaryAxesErrorMessage) : parameters.c;
  var coordinates = parameters.coordinates;
  var eulerAngles = parameters.eulerAngles;
  var feed = parameters.feed;
  if (feed === undefined && typeof gMotionModal !== "undefined") {
    feed = gMotionModal.getCurrent() !== 0;
  }
  var mode = parameters.mode;
  var performToolChange = mode == TOOLCHANGE;
  if (mode !== undefined && ![TCPON, TCPOFF, TWPON, TWPOFF, TOOLCHANGE, RETRACTTOOLAXIS].includes(mode)) {
    error(subst("Mode '%1' is not supported.", mode));
  }

  // mode takes precedence over TCP/TWP states
  var enableTCP = isTcpOn;
  var enableTWP = isTwpOn;
  if (mode === TCPON || mode === TCPOFF) {
    enableTCP = mode === TCPON;
  } else if (mode === TWPON || mode === TWPOFF) {
    enableTWP = mode === TWPON;
  } else {
    enableTCP = typeof state !== "undefined" && state.tcpIsActive;
    enableTWP = typeof state !== "undefined" && state.twpIsActive;
  }
  var disableTCP = !enableTCP;
  var disableTWP = !enableTWP;
  if (disableTWP) {
    simulation.setTWPModeOff();
    isTwpOn = false;
  }
  if (disableTCP) {
    simulation.setTCPModeOff();
    isTcpOn = false;
  }
  if (enableTCP) {
    simulation.setTCPModeOn();
    isTcpOn = true;
  }
  if (enableTWP) {
    if (settings.workPlaneMethod.eulerConvention == undefined) {
      simulation.setTWPModeAlignToCurrentPose();
    } else if (eulerAngles) {
      simulation.setTWPModeByEulerAngles(settings.workPlaneMethod.eulerConvention, eulerAngles.x, eulerAngles.y, eulerAngles.z);
    }
    isTwpOn = true;
  }
  if (mode == RETRACTTOOLAXIS) {
    simulation.retractAlongToolAxisToLimit();
  }

  if (debugSimulation) {
    writeln("  DEBUG" + JSON.stringify(parameters));
    writeln("  DEBUG" + JSON.stringify({isTwpOn:isTwpOn, isTcpOn:isTcpOn, feed:feed}));
  }

  if (x !== undefined || y !== undefined || z !== undefined || a !== undefined || b !== undefined || c !== undefined) {
    if (x !== undefined) {simulation.setTargetX(x);}
    if (y !== undefined) {simulation.setTargetY(y);}
    if (z !== undefined) {simulation.setTargetZ(z);}
    if (a !== undefined) {simulation.setTargetA(a);}
    if (b !== undefined) {simulation.setTargetB(b);}
    if (c !== undefined) {simulation.setTargetC(c);}

    if (feed != undefined && feed) {
      simulation.setMotionToLinear();
      simulation.setFeedrate(typeof feed == "number" ? feed : feedOutput.getCurrent() == 0 ? highFeedrate : feedOutput.getCurrent());
    } else {
      simulation.setMotionToRapid();
    }

    if (coordinates != undefined && coordinates == MACHINE) {
      simulation.moveToTargetInMachineCoords();
    } else {
      simulation.moveToTargetInWorkCoords();
    }
  }
  if (performToolChange) {
    simulation.performToolChangeCycle();
    simulation.moveToTargetInMachineCoords();
  }
}
// <<<<< INCLUDED FROM include_files/commonFunctions.cpi
// >>>>> INCLUDED FROM include_files/defineMachine.cpi
function defineMachine() {
  var useTCP = true;
  if (false) { // note: setup your machine here
    var aAxis = createAxis({coordinate:0, table:true, axis:[1, 0, 0], range:[-120, 120], preference:1, tcp:useTCP});
    var cAxis = createAxis({coordinate:2, table:true, axis:[0, 0, 1], range:[-360, 360], preference:0, tcp:useTCP});
    machineConfiguration = new MachineConfiguration(aAxis, cAxis);

    setMachineConfiguration(machineConfiguration);
    if (receivedMachineConfiguration) {
      warning(localize("The provided CAM machine configuration is overwritten by the postprocessor."));
      receivedMachineConfiguration = false; // CAM provided machine configuration is overwritten
    }
  }

  if (!receivedMachineConfiguration) {
    // multiaxis settings
    if (machineConfiguration.isHeadConfiguration()) {
      machineConfiguration.setVirtualTooltip(false); // translate the pivot point to the virtual tool tip for nonTCP rotary heads
    }

    // retract / reconfigure
    var performRewinds = false; // set to true to enable the rewind/reconfigure logic
    if (performRewinds) {
      machineConfiguration.enableMachineRewinds(); // enables the retract/reconfigure logic
      safeRetractDistance = (unit == IN) ? 1 : 25; // additional distance to retract out of stock, can be overridden with a property
      safeRetractFeed = (unit == IN) ? 20 : 500; // retract feed rate
      safePlungeFeed = (unit == IN) ? 10 : 250; // plunge feed rate
      machineConfiguration.setSafeRetractDistance(safeRetractDistance);
      machineConfiguration.setSafeRetractFeedrate(safeRetractFeed);
      machineConfiguration.setSafePlungeFeedrate(safePlungeFeed);
      var stockExpansion = new Vector(toPreciseUnit(0.1, IN), toPreciseUnit(0.1, IN), toPreciseUnit(0.1, IN)); // expand stock XYZ values
      machineConfiguration.setRewindStockExpansion(stockExpansion);
    }

    // multi-axis feedrates
    if (machineConfiguration.isMultiAxisConfiguration()) {
      machineConfiguration.setMultiAxisFeedrate(
        useTCP ? (useTCPInverseTimeFeed() ? FEED_INVERSE_TIME : FEED_FPM) : getProperty("useDPMFeeds") ? FEED_DPM : FEED_INVERSE_TIME,
        9999.99, // maximum output value for inverse time feed rates
        useTCP ? getTCPInverseTimeUnits() : getProperty("useDPMFeeds") ? DPM_COMBINATION : INVERSE_MINUTES, // INVERSE_MINUTES/INVERSE_SECONDS or DPM_COMBINATION/DPM_STANDARD
        0.5, // tolerance to determine when the DPM feed has changed
        1.0 // ratio of rotary accuracy to linear accuracy for DPM calculations
      );
      setMachineConfiguration(machineConfiguration);
    }

    /* home positions */
    // machineConfiguration.setHomePositionX(toPreciseUnit(0, IN));
    // machineConfiguration.setHomePositionY(toPreciseUnit(0, IN));
    // machineConfiguration.setRetractPlane(toPreciseUnit(0, IN));
  }
}
// <<<<< INCLUDED FROM include_files/defineMachine.cpi
// >>>>> INCLUDED FROM include_files/defineWorkPlane.cpi
validate(settings.workPlaneMethod, "Setting 'workPlaneMethod' is required but not defined.");
function defineWorkPlane(_section, _setWorkPlane) {
  var abc = new Vector(0, 0, 0);
  var sectionUsesTCP = isTCPSupportedByOperation(_section);
  if (settings.workPlaneMethod.forceMultiAxisIndexing || !is3D() || machineConfiguration.isMultiAxisConfiguration()) {
    if (isPolarModeActive()) {
      abc = getCurrentDirection();
    } else if (_section.isMultiAxis()) {
      forceWorkPlane();
      cancelTransformation();
      abc = _section.isOptimizedForMachine() ? _section.getInitialToolAxisABC() : _section.getGlobalInitialToolAxis();
    } else if (settings.workPlaneMethod.useTiltedWorkplane && settings.workPlaneMethod.eulerConvention != undefined) {
      if (settings.workPlaneMethod.eulerCalculationMethod == "machine" && machineConfiguration.isMultiAxisConfiguration()) {
        abc = machineConfiguration.getOrientation(getWorkPlaneMachineABC(_section, true)).getEuler2(settings.workPlaneMethod.eulerConvention);
      } else {
        abc = _section.workPlane.getEuler2(settings.workPlaneMethod.eulerConvention);
      }
    } else {
      abc = getWorkPlaneMachineABC(_section, true);
    }

    if (_setWorkPlane) {
      if (_section.isMultiAxis() || isPolarModeActive() || sectionUsesTCP) { // 4-5x simultaneous or forced TCP operations
        cancelWorkPlane();
        if (_section.isOptimizedForMachine() && !sectionUsesTCP) {
          positionABC(abc, true);
        } else {
          setCurrentDirection(abc);
        }
      } else { // 3x and/or 3+2x operations
        setWorkPlane(abc);
      }
    }
  } else {
    var remaining = _section.workPlane;
    if (!isSameDirection(remaining.forward, new Vector(0, 0, 1))) {
      error(localize("Tool orientation is not supported."));
      return abc;
    }
    setRotation(remaining);
  }
  tcp.isSupportedByOperation = sectionUsesTCP;
  return abc;
}

function isTCPSupportedByOperation(_section) {
  if (forceTCPForIndexedSections() && isMatsuuraIndexed3Plus2Section(_section)) {
    return tcp.isSupportedByControl && tcp.isSupportedByMachine;
  }
  var _tcp = _section.getOptimizedTCPMode() == OPTIMIZE_NONE;
  if (!_section.isMultiAxis() && (settings.workPlaneMethod.useTiltedWorkplane ||
    (machineConfiguration.isMultiAxisConfiguration() && settings.workPlaneMethod.optimizeType != undefined ?
      getWorkPlaneMachineABC(_section, false).isZero() : isSameDirection(machineConfiguration.getSpindleAxis(), getForwardDirection(_section))) ||
    settings.workPlaneMethod.optimizeType == OPTIMIZE_HEADS ||
    settings.workPlaneMethod.optimizeType == OPTIMIZE_TABLES ||
    settings.workPlaneMethod.optimizeType == OPTIMIZE_BOTH)) {
    _tcp = false;
  }
  return _tcp;
}

function getTCPEntryABCForSection(_section) {
  if (_section.isMultiAxis()) {
    return _section.isOptimizedForMachine() ? _section.getInitialToolAxisABC() : _section.getGlobalInitialToolAxis();
  }
  return getWorkPlaneMachineABC(_section, false);
}
// <<<<< INCLUDED FROM include_files/defineWorkPlane.cpi
// >>>>> INCLUDED FROM include_files/getWorkPlaneMachineABC.cpi
validate(settings.machineAngles, "Setting 'machineAngles' is required but not defined.");
function getWorkPlaneMachineABC(_section, rotate) {
  var currentABC = isFirstSection() ? new Vector(0, 0, 0) : getCurrentABC();
  var abc = _section.getABCByPreference(machineConfiguration, _section.workPlane, currentABC, settings.machineAngles.controllingAxis, settings.machineAngles.type, settings.machineAngles.options);
  if (!isSameDirection(machineConfiguration.getDirection(abc), _section.workPlane.forward)) {
    error(localize("Orientation not supported."));
  }
  if (rotate) {
    if (settings.workPlaneMethod.optimizeType == undefined || settings.workPlaneMethod.useTiltedWorkplane) { // legacy
      var useTCP = false;
      var R = machineConfiguration.getRemainingOrientation(abc, _section.workPlane);
      setRotation(useTCP ? _section.workPlane : R);
    } else {
      if (!_section.isOptimizedForMachine()) {
        machineConfiguration.setToolLength(getSetting("workPlaneMethod.compensateToolLength", false) ? getBodyLength(_section.getTool()) : 0); // define the tool length for head adjustments
        _section.optimize3DPositionsByMachine(machineConfiguration, abc, settings.workPlaneMethod.optimizeType);
      }
    }
  }
  return abc;
}
// <<<<< INCLUDED FROM include_files/getWorkPlaneMachineABC.cpi
// >>>>> INCLUDED FROM include_files/positionABC.cpi
function positionABC(abc, force) {
  if (!machineConfiguration.isMultiAxisConfiguration()) {
    error("Function 'positionABC' can only be used with multi-axis machine configurations.");
  }
  if (typeof unwindABC == "function") {
    unwindABC(abc);
  }
  if (force) {
    forceABC();
  }
  var a = aOutput.format(abc.x);
  var b = bOutput.format(abc.y);
  var c = cOutput.format(abc.z);
  if (a || b || c) {
    writeRetract(Z);
    if (getSetting("retract.homeXY.onIndexing", false)) {
      writeRetract(settings.retract.homeXY.onIndexing);
    }
    onCommand(COMMAND_UNLOCK_MULTI_AXIS);
    gMotionModal.reset();
    writeBlock(gMotionModal.format(0), a, b, c);
    setCurrentABC(abc); // required for machine simulation
    machineSimulation({a:abc.x, b:abc.y, c:abc.z, coordinates:MACHINE});
  }
}
// <<<<< INCLUDED FROM include_files/positionABC.cpi
// >>>>> INCLUDED FROM include_files/writeWCS.cpi
function writeWCS(section, wcsIsRequired) {
  if (section.workOffset != currentWorkOffset) {
    if (getSetting("workPlaneMethod.cancelTiltFirst", false) && wcsIsRequired) {
      cancelWorkPlane();
    }
    if (typeof forceWorkPlane == "function" && wcsIsRequired) {
      forceWorkPlane();
    }
    writeStartBlocks(wcsIsRequired, function () {
      writeBlock(section.wcs);
    });
    currentWorkOffset = section.workOffset;
  }
}
// <<<<< INCLUDED FROM include_files/writeWCS.cpi
// >>>>> INCLUDED FROM include_files/writeToolCall.cpi
function writeToolCall(tool, insertToolCall) {
  if (!isFirstSection()) {
    writeStartBlocks(!getProperty("safeStartAllOperations") && insertToolCall, function () {
      writeRetract(Z); // write optional Z retract before tool change if safeStartAllOperations is enabled
    });
  }
  writeStartBlocks(insertToolCall, function () {
    writeRetract(Z);
    if (getSetting("retract.homeXY.onToolChange", false)) {
      writeRetract(settings.retract.homeXY.onToolChange);
    }
    if (!isFirstSection() && insertToolCall) {
      if (typeof forceWorkPlane == "function") {
        forceWorkPlane();
      }
      onCommand(COMMAND_COOLANT_OFF); // turn off coolant on tool change
      if (typeof disableLengthCompensation == "function") {
        disableLengthCompensation(false);
      }
    }

    if (tool.manualToolChange) {
      onCommand(COMMAND_STOP);
      writeComment("MANUAL TOOL CHANGE TO T" + toolFormat.format(tool.number));
    } else {
      if (!isFirstSection() && getProperty("optionalStop") && insertToolCall) {
        onCommand(COMMAND_OPTIONAL_STOP);
      }
      onCommand(COMMAND_LOAD_TOOL);
    }
  });
  if (typeof forceModals == "function" && (insertToolCall || getProperty("safeStartAllOperations"))) {
    forceModals();
  }
}
// <<<<< INCLUDED FROM include_files/writeToolCall.cpi
// >>>>> INCLUDED FROM include_files/startSpindle.cpi
function startSpindle(tool, insertToolCall) {
  if (tool.type != TOOL_PROBE) {
    var spindleSpeedIsRequired = insertToolCall || forceSpindleSpeed || isFirstSection() ||
      rpmFormat.areDifferent(spindleSpeed, sOutput.getCurrent()) ||
      (tool.clockwise != getPreviousSection().getTool().clockwise);

    writeStartBlocks(spindleSpeedIsRequired, function () {
      if (spindleSpeedIsRequired || operationNeedsSafeStart) {
        onCommand(COMMAND_START_SPINDLE);
      }
    });
  }
}
// <<<<< INCLUDED FROM include_files/startSpindle.cpi
// >>>>> INCLUDED FROM include_files/parametricFeeds.cpi
properties.useParametricFeed = {
  title      : "Parametric feed",
  description: "Specifies that the feedrates should be output using parameters. TH: ให้ feed ออกเป็น parameter เช่น F# แทนตัวเลขตรงๆ ใช้เฉพาะเมื่อรู้ว่าต้องการแบบนี้.",
  group      : "preferences",
  type       : "boolean",
  value      : false,
  visible    : false,
  scope      : "post"
};
var activeMovements;
var currentFeedId;
validate(settings.parametricFeeds, "Setting 'parametricFeeds' is required but not defined.");
function initializeParametricFeeds(insertToolCall) {
  if (getProperty("useParametricFeed") && getParameter("operation-strategy") != "drill" && !currentSection.hasAnyCycle()) {
    if (!insertToolCall && activeMovements && (getCurrentSectionId() > 0) &&
      ((getPreviousSection().getPatternId() == currentSection.getPatternId()) && (currentSection.getPatternId() != 0))) {
      return; // use the current feeds
    }
  } else {
    activeMovements = undefined;
    return;
  }

  activeMovements = new Array();
  var movements = currentSection.getMovements();

  var id = 0;
  var activeFeeds = new Array();
  if (hasParameter("operation:tool_feedCutting")) {
    if (movements & ((1 << MOVEMENT_CUTTING) | (1 << MOVEMENT_LINK_TRANSITION) | (1 << MOVEMENT_EXTENDED))) {
      var feedContext = new FeedContext(id, localize("Cutting"), getParameter("operation:tool_feedCutting"));
      activeFeeds.push(feedContext);
      activeMovements[MOVEMENT_CUTTING] = feedContext;
      if (!hasParameter("operation:tool_feedTransition")) {
        activeMovements[MOVEMENT_LINK_TRANSITION] = feedContext;
      }
      activeMovements[MOVEMENT_EXTENDED] = feedContext;
    }
    ++id;
    if (movements & (1 << MOVEMENT_PREDRILL)) {
      feedContext = new FeedContext(id, localize("Predrilling"), getParameter("operation:tool_feedCutting"));
      activeMovements[MOVEMENT_PREDRILL] = feedContext;
      activeFeeds.push(feedContext);
    }
    ++id;
  }
  if (hasParameter("operation:finishFeedrate")) {
    if (movements & (1 << MOVEMENT_FINISH_CUTTING)) {
      var feedContext = new FeedContext(id, localize("Finish"), getParameter("operation:finishFeedrate"));
      activeFeeds.push(feedContext);
      activeMovements[MOVEMENT_FINISH_CUTTING] = feedContext;
    }
    ++id;
  } else if (hasParameter("operation:tool_feedCutting")) {
    if (movements & (1 << MOVEMENT_FINISH_CUTTING)) {
      var feedContext = new FeedContext(id, localize("Finish"), getParameter("operation:tool_feedCutting"));
      activeFeeds.push(feedContext);
      activeMovements[MOVEMENT_FINISH_CUTTING] = feedContext;
    }
    ++id;
  }
  if (hasParameter("operation:tool_feedEntry")) {
    if (movements & (1 << MOVEMENT_LEAD_IN)) {
      var feedContext = new FeedContext(id, localize("Entry"), getParameter("operation:tool_feedEntry"));
      activeFeeds.push(feedContext);
      activeMovements[MOVEMENT_LEAD_IN] = feedContext;
    }
    ++id;
  }
  if (hasParameter("operation:tool_feedExit")) {
    if (movements & (1 << MOVEMENT_LEAD_OUT)) {
      var feedContext = new FeedContext(id, localize("Exit"), getParameter("operation:tool_feedExit"));
      activeFeeds.push(feedContext);
      activeMovements[MOVEMENT_LEAD_OUT] = feedContext;
    }
    ++id;
  }
  if (hasParameter("operation:noEngagementFeedrate")) {
    if (movements & (1 << MOVEMENT_LINK_DIRECT)) {
      var feedContext = new FeedContext(id, localize("Direct"), getParameter("operation:noEngagementFeedrate"));
      activeFeeds.push(feedContext);
      activeMovements[MOVEMENT_LINK_DIRECT] = feedContext;
    }
    ++id;
  } else if (hasParameter("operation:tool_feedCutting") &&
             hasParameter("operation:tool_feedEntry") &&
             hasParameter("operation:tool_feedExit")) {
    if (movements & (1 << MOVEMENT_LINK_DIRECT)) {
      var feedContext = new FeedContext(id, localize("Direct"), Math.max(getParameter("operation:tool_feedCutting"), getParameter("operation:tool_feedEntry"), getParameter("operation:tool_feedExit")));
      activeFeeds.push(feedContext);
      activeMovements[MOVEMENT_LINK_DIRECT] = feedContext;
    }
    ++id;
  }
  if (hasParameter("operation:reducedFeedrate")) {
    if (movements & (1 << MOVEMENT_REDUCED)) {
      var feedContext = new FeedContext(id, localize("Reduced"), getParameter("operation:reducedFeedrate"));
      activeFeeds.push(feedContext);
      activeMovements[MOVEMENT_REDUCED] = feedContext;
    }
    ++id;
  }
  if (hasParameter("operation:tool_feedRamp")) {
    if (movements & ((1 << MOVEMENT_RAMP) | (1 << MOVEMENT_RAMP_HELIX) | (1 << MOVEMENT_RAMP_PROFILE) | (1 << MOVEMENT_RAMP_ZIG_ZAG))) {
      var feedContext = new FeedContext(id, localize("Ramping"), getParameter("operation:tool_feedRamp"));
      activeFeeds.push(feedContext);
      activeMovements[MOVEMENT_RAMP] = feedContext;
      activeMovements[MOVEMENT_RAMP_HELIX] = feedContext;
      activeMovements[MOVEMENT_RAMP_PROFILE] = feedContext;
      activeMovements[MOVEMENT_RAMP_ZIG_ZAG] = feedContext;
    }
    ++id;
  }
  if (hasParameter("operation:tool_feedPlunge")) {
    if (movements & (1 << MOVEMENT_PLUNGE)) {
      var feedContext = new FeedContext(id, localize("Plunge"), getParameter("operation:tool_feedPlunge"));
      activeFeeds.push(feedContext);
      activeMovements[MOVEMENT_PLUNGE] = feedContext;
    }
    ++id;
  }
  if (true) { // high feed
    if ((movements & (1 << MOVEMENT_HIGH_FEED)) || (highFeedMapping != HIGH_FEED_NO_MAPPING)) {
      var feed;
      if (hasParameter("operation:highFeedrateMode") && getParameter("operation:highFeedrateMode") != "disabled") {
        feed = getParameter("operation:highFeedrate");
      } else {
        feed = this.highFeedrate;
      }
      var feedContext = new FeedContext(id, localize("High Feed"), feed);
      activeFeeds.push(feedContext);
      activeMovements[MOVEMENT_HIGH_FEED] = feedContext;
      activeMovements[MOVEMENT_RAPID] = feedContext;
    }
    ++id;
  }
  if (hasParameter("operation:tool_feedTransition")) {
    if (movements & (1 << MOVEMENT_LINK_TRANSITION)) {
      var feedContext = new FeedContext(id, localize("Transition"), getParameter("operation:tool_feedTransition"));
      activeFeeds.push(feedContext);
      activeMovements[MOVEMENT_LINK_TRANSITION] = feedContext;
    }
    ++id;
  }

  for (var i = 0; i < activeFeeds.length; ++i) {
    var feedContext = activeFeeds[i];
    var feedDescription = typeof formatComment == "function" ? formatComment(feedContext.description) : feedContext.description;
    writeBlock(settings.parametricFeeds.feedAssignmentVariable + (settings.parametricFeeds.firstFeedParameter + feedContext.id) + "=" + feedFormat.format(feedContext.feed) + SP + feedDescription);
  }
}

function FeedContext(id, description, feed) {
  this.id = id;
  this.description = description;
  this.feed = feed;
}
// <<<<< INCLUDED FROM include_files/parametricFeeds.cpi
// >>>>> INCLUDED FROM include_files/coolant.cpi
var currentCoolantMode = COOLANT_OFF;
var coolantOff = undefined;
var isOptionalCoolant = false;
var forceCoolant = false;

function setCoolant(coolant) {
  var coolantCodes = getCoolantCodes(coolant);
  if (Array.isArray(coolantCodes)) {
    writeStartBlocks(!isOptionalCoolant, function () {
      if (settings.coolant.singleLineCoolant) {
        writeBlock(coolantCodes.join(getWordSeparator()));
      } else {
        for (var c in coolantCodes) {
          writeBlock(coolantCodes[c]);
        }
      }
    });
    return undefined;
  }
  return coolantCodes;
}

function getCoolantCodes(coolant, format) {
  if (!getProperty("useCoolant", true)) {
    return undefined; // coolant output is disabled by property if it exists
  }
  isOptionalCoolant = false;
  if (typeof operationNeedsSafeStart == "undefined") {
    operationNeedsSafeStart = false;
  }
  var multipleCoolantBlocks = new Array(); // create a formatted array to be passed into the outputted line
  var coolants = settings.coolant.coolants;
  if (!coolants) {
    error(localize("Coolants have not been defined."));
  }
  if (tool.type && tool.type == TOOL_PROBE) { // avoid coolant output for probing
    coolant = COOLANT_OFF;
  }
  if (coolant == currentCoolantMode) {
    if (operationNeedsSafeStart && coolant != COOLANT_OFF) {
      isOptionalCoolant = true;
    } else if (!forceCoolant || coolant == COOLANT_OFF) {
      return undefined; // coolant is already active
    }
  }
  if ((coolant != COOLANT_OFF) && (currentCoolantMode != COOLANT_OFF) && (coolantOff != undefined) && !forceCoolant && !isOptionalCoolant) {
    if (Array.isArray(coolantOff)) {
      for (var i in coolantOff) {
        multipleCoolantBlocks.push(coolantOff[i]);
      }
    } else {
      multipleCoolantBlocks.push(coolantOff);
    }
  }
  forceCoolant = false;

  var m;
  var coolantCodes = {};
  for (var c in coolants) { // find required coolant codes into the coolants array
    if (coolants[c].id == coolant) {
      coolantCodes.on = coolants[c].on;
      if (coolants[c].off != undefined) {
        coolantCodes.off = coolants[c].off;
        break;
      } else {
        for (var i in coolants) {
          if (coolants[i].id == COOLANT_OFF) {
            coolantCodes.off = coolants[i].off;
            break;
          }
        }
      }
    }
  }
  if (coolant == COOLANT_OFF) {
    m = !coolantOff ? coolantCodes.off : coolantOff; // use the default coolant off command when an 'off' value is not specified
  } else {
    coolantOff = coolantCodes.off;
    m = coolantCodes.on;
  }

  if (!m) {
    onUnsupportedCoolant(coolant);
    m = 9;
  } else {
    if (Array.isArray(m)) {
      for (var i in m) {
        multipleCoolantBlocks.push(m[i]);
      }
    } else {
      multipleCoolantBlocks.push(m);
    }
    currentCoolantMode = coolant;
    for (var i in multipleCoolantBlocks) {
      if (typeof multipleCoolantBlocks[i] == "number") {
        multipleCoolantBlocks[i] = mFormat.format(multipleCoolantBlocks[i]);
      }
    }
    if (format == undefined || format) {
      return multipleCoolantBlocks; // return the single formatted coolant value
    } else {
      return m; // return unformatted coolant value
    }
  }
  return undefined;
}
// <<<<< INCLUDED FROM include_files/coolant.cpi
// >>>>> INCLUDED FROM include_files/smoothing.cpi
// collected state below, do not edit
validate(settings.smoothing, "Setting 'smoothing' is required but not defined.");
var smoothing = {
  cancel     : false, // cancel tool length prior to update smoothing for this operation
  isActive   : false, // the current state of smoothing
  isAllowed  : false, // smoothing is allowed for this operation
  isDifferent: false, // tells if smoothing levels/tolerances/both are different between operations
  level      : -1, // the active level of smoothing
  tolerance  : -1, // the current operation tolerance
  force      : false // smoothing needs to be forced out in this operation
};

function initializeSmoothing(_section) {
  var _section = _section !== undefined ? _section : currentSection;
  var smoothingSettings = settings.smoothing;
  var previousLevel = smoothing.level;
  var previousTolerance = xyzFormat.getResultingValue(smoothing.tolerance);

  // format threshold parameters
  var thresholdRoughing = xyzFormat.getResultingValue(smoothingSettings.thresholdRoughing);
  var thresholdSemiFinishing = xyzFormat.getResultingValue(smoothingSettings.thresholdSemiFinishing);
  var thresholdFinishing = xyzFormat.getResultingValue(smoothingSettings.thresholdFinishing);

  // determine new smoothing levels and tolerances
  smoothing.level = parseInt(_section.getProperty("useSmoothing"), 10);
  smoothing.level = isNaN(smoothing.level) ? -1 : smoothing.level;
  smoothing.tolerance = xyzFormat.getResultingValue(Math.max(_section.getParameter("operation:tolerance", thresholdFinishing), 0));

  if (smoothing.level == 9999) {
    if (smoothingSettings.autoLevelCriteria == "stock") { // determine auto smoothing level based on stockToLeave
      var stockToLeave = xyzFormat.getResultingValue(_section.getParameter("operation:stockToLeave", _section.getParameter("operation:verticalStockToLeave", 0)));
      var verticalStockToLeave = xyzFormat.getResultingValue(_section.getParameter("operation:verticalStockToLeave", stockToLeave));
      if (((stockToLeave >= thresholdRoughing) && (verticalStockToLeave >= thresholdRoughing)) || _section.getParameter("operation:strategy", "") == "face") {
        smoothing.level = smoothingSettings.roughing; // set roughing level
      } else {
        if (((stockToLeave >= thresholdSemiFinishing) && (stockToLeave < thresholdRoughing)) &&
          ((verticalStockToLeave >= thresholdSemiFinishing) && (verticalStockToLeave < thresholdRoughing))) {
          smoothing.level = smoothingSettings.semi; // set semi level
        } else if (((stockToLeave >= thresholdFinishing) && (stockToLeave < thresholdSemiFinishing)) &&
          ((verticalStockToLeave >= thresholdFinishing) && (verticalStockToLeave < thresholdSemiFinishing))) {
          smoothing.level = smoothingSettings.semifinishing; // set semi-finishing level
        } else {
          smoothing.level = smoothingSettings.finishing; // set finishing level
        }
      }
    } else { // detemine auto smoothing level based on operation tolerance instead of stockToLeave
      if (smoothing.tolerance >= thresholdRoughing || _section.getParameter("operation:strategy", "") == "face") {
        smoothing.level = smoothingSettings.roughing; // set roughing level
      } else {
        if (((smoothing.tolerance >= thresholdSemiFinishing) && (smoothing.tolerance < thresholdRoughing))) {
          smoothing.level = smoothingSettings.semi; // set semi level
        } else if (((smoothing.tolerance >= thresholdFinishing) && (smoothing.tolerance < thresholdSemiFinishing))) {
          smoothing.level = smoothingSettings.semifinishing; // set semi-finishing level
        } else {
          smoothing.level = smoothingSettings.finishing; // set finishing level
        }
      }
    }
  }
  if (isMatsuuraTCPOutputSection(_section)) {
    smoothing.level = getMatsuuraTCPSmoothingLevel(smoothing.level);
  }

  if (smoothing.level == -1) { // useSmoothing is disabled
    smoothing.isAllowed = false;
  } else {
    smoothing.isAllowed = !(_section.getTool().type == TOOL_PROBE || isDrillingCycle(_section)) || (_section.isConnectionSection && _section.isConnectionSection() && _section.isMultiAxis());
    if (isFirstSection()) {
      smoothing.isActive = undefined;
    }
  }
  if (!smoothing.isAllowed) {
    smoothing.level = -1;
    smoothing.tolerance = -1;
  }

  switch (smoothingSettings.differenceCriteria) {
  case "level":
    smoothing.isDifferent = smoothing.level != previousLevel;
    break;
  case "tolerance":
    smoothing.isDifferent = smoothing.tolerance != previousTolerance;
    break;
  case "both":
    smoothing.isDifferent = smoothing.level != previousLevel || smoothing.tolerance != previousTolerance;
    break;
  default:
    error(localize("Unsupported smoothing criteria."));
    return;
  }

  // tool length compensation needs to be canceled when smoothing state/level changes
  if (smoothingSettings.cancelCompensation) {
    smoothing.cancel = !isFirstSection() && smoothing.isDifferent;
  }
}
// <<<<< INCLUDED FROM include_files/smoothing.cpi
// >>>>> INCLUDED FROM include_files/writeProgramHeader.cpi
properties.writeMachine = {
  title      : "Write machine",
  description: "Output the machine settings in the header of the program. TH: ใส่ข้อมูลเครื่องไว้หัวโปรแกรม เพื่อดูว่าโพสด้วย machine ไหน.",
  group      : "formats",
  type       : "boolean",
  value      : true,
  scope      : "post"
};
properties.writeTools = {
  title      : "Write tool list",
  description: "Output a tool list in the header of the program. TH: ใส่รายการดอกไว้หัวโปรแกรม ช่วยตรวจ T/H/D ก่อนรันงาน.",
  group      : "formats",
  type       : "boolean",
  value      : true,
  scope      : "post"
};
function writeProgramHeader() {
  // dump machine configuration
  var vendor = machineConfiguration.getVendor();
  var model = machineConfiguration.getModel();
  var mDescription = machineConfiguration.getDescription();
  if (getProperty("writeMachine") && (vendor || model || mDescription)) {
    writeComment(localize("Machine"));
    if (vendor) {
      writeComment("  " + localize("vendor") + ": " + vendor);
    }
    if (model) {
      writeComment("  " + localize("model") + ": " + model);
    }
    if (mDescription) {
      writeComment("  " + localize("description") + ": " + mDescription);
    }
  }

  // dump tool information
  if (getProperty("writeTools")) {
    if (false) { // set to true to use the post kernel version of the tool list
      writeToolTable(TOOL_NUMBER_COL);
    } else {
      var zRanges = {};
      if (is3D()) {
        var numberOfSections = getNumberOfSections();
        for (var i = 0; i < numberOfSections; ++i) {
          var section = getSection(i);
          var zRange = section.getGlobalZRange();
          var tool = section.getTool();
          if (zRanges[tool.number]) {
            zRanges[tool.number].expandToRange(zRange);
          } else {
            zRanges[tool.number] = zRange;
          }
        }
      }
      var tools = getToolTable();
      if (tools.getNumberOfTools() > 0) {
        for (var i = 0; i < tools.getNumberOfTools(); ++i) {
          var tool = tools.getTool(i);
          var comment = (getProperty("toolAsName") ? "\"" + tool.description.toUpperCase() + "\"" : "T" + toolFormat.format(tool.number)) + " " +
          "D=" + xyzFormat.format(tool.diameter) + " " +
          localize("CR") + "=" + xyzFormat.format(tool.cornerRadius);
          if ((tool.taperAngle > 0) && (tool.taperAngle < Math.PI)) {
            comment += " " + localize("TAPER") + "=" + taperFormat.format(tool.taperAngle) + localize("deg");
          }
          if (zRanges[tool.number]) {
            comment += " - " + localize("ZMIN") + "=" + xyzFormat.format(zRanges[tool.number].getMinimum());
          }
          comment += " - " + getToolTypeName(tool.type);
          writeComment(comment);
        }
      }
    }
  }
}
// <<<<< INCLUDED FROM include_files/writeProgramHeader.cpi
// >>>>> INCLUDED FROM include_files/subprograms.cpi
properties.useSubroutines = {
  title      : "Use subroutines",
  description: "Select your desired subroutine option. 'All Operations' creates subroutines per each operation, 'Cycles' creates subroutines for cycle operations on same holes, and 'Patterns' creates subroutines for patterned operations. TH: เลือกว่าจะใช้ subprogram หรือไม่ ถ้าไม่แน่ใจให้ใช้ No เพื่อให้อ่าน NC ง่าย.",
  group      : "preferences",
  type       : "enum",
  values     : [
    {title:"No", id:"none"},
    {title:"All Operations", id:"allOperations"},
    {title:"All Operations & Patterns", id:"allPatterns"},
    {title:"Cycles", id:"cycles"},
    {title:"Operations, Patterns, Cycles", id:"all"},
    {title:"Patterns", id:"patterns"}
  ],
  value: "none",
  visible: false,
  scope: "post"
};
properties.useFilesForSubprograms = {
  title      : "Use files for subroutines",
  description: "If enabled, subroutines will be saved as individual files. TH: ถ้าเปิด จะบันทึก subprogram แยกเป็นไฟล์ต่างหาก.",
  group      : "preferences",
  type       : "boolean",
  value      : false,
  visible    : false,
  scope      : "post"
};

var NONE = 0x0000;
var PATTERNS = 0x0001;
var CYCLES = 0x0010;
var ALLOPERATIONS = 0x0100;
var subroutineBitmasks = {
  none         : NONE,
  patterns     : PATTERNS,
  cycles       : CYCLES,
  allOperations: ALLOPERATIONS,
  allPatterns  : PATTERNS + ALLOPERATIONS,
  all          : PATTERNS + CYCLES + ALLOPERATIONS
};

var SUB_UNKNOWN = 0;
var SUB_PATTERN = 1;
var SUB_CYCLE = 2;

// collected state below, do not edit
validate(settings.subprograms, "Setting 'subprograms' is required but not defined.");
var subprogramState = {
  subprograms            : [],          // Redirection buffer
  newSubprogram          : false,       // Indicate if the current subprogram is new to definedSubprograms
  currentSubprogram      : 0,           // The current subprogram number
  lastSubprogram         : undefined,   // The last subprogram number
  definedSubprograms     : new Array(), // A collection of pattern and cycle subprograms
  saveShowSequenceNumbers: "",          // Used to store pre-condition of "showSequenceNumbers"
  cycleSubprogramIsActive: false,       // Indicate if it's handling a cycle subprogram
  patternIsActive        : false,       // Indicate if it's handling a pattern subprogram
  incrementalSubprogram  : false,       // Indicate if the current subprogram needs to go incremental mode
  incrementalMode        : false,       // Indicate if incremental mode is on
  mainProgramNumber      : undefined    // The main program number
};

function subprogramResolveSetting(_setting, _val, _comment) {
  if (typeof _setting == "string") {
    return formatWords(_setting.toString().replace("%currentSubprogram", subprogramState.currentSubprogram), (_comment ? formatComment(_comment) : ""));
  } else {
    return formatWords(_setting + (_val ? settings.subprograms.format.format(_val) : ""), (_comment ? formatComment(_comment) : ""));
  }
}

/**
 * Start to redirect buffer to subprogram.
 * @param {Vector} initialPosition Initial position
 * @param {Vector} abc Machine axis angles
 * @param {boolean} incremental If the subprogram needs to go incremental mode
 */
function subprogramStart(initialPosition, abc, incremental) {
  var comment = getParameter("operation-comment", "");
  var startBlock;
  if (getProperty("useFilesForSubprograms")) {
    var _fileName = subprogramState.currentSubprogram;
    var subprogramExtension = extension;
    if (settings.subprograms.files) {
      if (settings.subprograms.files.prefix != undefined) {
        _fileName = subprogramResolveSetting(settings.subprograms.files.prefix, subprogramState.currentSubprogram);
      }
      if (settings.subprograms.files.extension) {
        subprogramExtension = settings.subprograms.files.extension;
      }
    }
    var path = FileSystem.getCombinedPath(FileSystem.getFolderPath(getOutputPath()), _fileName + "." + subprogramExtension);
    redirectToFile(path);
    startBlock = subprogramResolveSetting(settings.subprograms.startBlock.files, subprogramState.currentSubprogram, comment);
  } else {
    redirectToBuffer();
    startBlock = subprogramResolveSetting(settings.subprograms.startBlock.embedded, subprogramState.currentSubprogram, comment);
  }
  writeln(startBlock);

  subprogramState.saveShowSequenceNumbers = getProperty("showSequenceNumbers", undefined);
  if (subprogramState.saveShowSequenceNumbers != undefined) {
    setProperty("showSequenceNumbers", "false");
  }
  if (incremental) {
    setAbsIncMode(true, initialPosition, abc);
  }
  if (typeof gPlaneModal != "undefined" && typeof gMotionModal != "undefined") {
    forceModals(gPlaneModal, gMotionModal);
  }
}

/** Output the command for calling a subprogram by its subprogram number. */
function subprogramCall() {
  var callBlock;
  if (getProperty("useFilesForSubprograms")) {
    callBlock = subprogramResolveSetting(settings.subprograms.callBlock.files, subprogramState.currentSubprogram);
  } else {
    callBlock = subprogramResolveSetting(settings.subprograms.callBlock.embedded, subprogramState.currentSubprogram);
  }
  writeBlock(callBlock); // call subprogram
}

/** End of subprogram and close redirection. */
function subprogramEnd() {
  if (isRedirecting()) {
    if (subprogramState.newSubprogram) {
      var finalPosition = getFramePosition(currentSection.getFinalPosition());
      var abc;
      if (currentSection.isMultiAxis() && machineConfiguration.isMultiAxisConfiguration()) {
        abc = currentSection.getFinalToolAxisABC();
      } else {
        abc = getCurrentDirection();
      }
      setAbsIncMode(false, finalPosition, abc);

      if (getProperty("useFilesForSubprograms")) {
        var endBlockFiles = subprogramResolveSetting(settings.subprograms.endBlock.files);
        writeln(endBlockFiles);
      } else {
        var endBlockEmbedded = subprogramResolveSetting(settings.subprograms.endBlock.embedded);
        writeln(endBlockEmbedded);
        writeln("");
        subprogramState.subprograms += getRedirectionBuffer();
      }
    }
    forceAny();
    subprogramState.newSubprogram = false;
    subprogramState.cycleSubprogramIsActive = false;
    if (subprogramState.saveShowSequenceNumbers != undefined) {
      setProperty("showSequenceNumbers", subprogramState.saveShowSequenceNumbers);
    }
    closeRedirection();
  }
}

/** Returns true if the spatial vectors are significantly different. */
function areSpatialVectorsDifferent(_vector1, _vector2) {
  return (xyzFormat.getResultingValue(_vector1.x) != xyzFormat.getResultingValue(_vector2.x)) ||
    (xyzFormat.getResultingValue(_vector1.y) != xyzFormat.getResultingValue(_vector2.y)) ||
    (xyzFormat.getResultingValue(_vector1.z) != xyzFormat.getResultingValue(_vector2.z));
}

/** Returns true if the spatial boxes are a pure translation. */
function areSpatialBoxesTranslated(_box1, _box2) {
  return !areSpatialVectorsDifferent(Vector.diff(_box1[1], _box1[0]), Vector.diff(_box2[1], _box2[0])) &&
    !areSpatialVectorsDifferent(Vector.diff(_box2[0], _box1[0]), Vector.diff(_box2[1], _box1[1]));
}

/** Returns true if the spatial boxes are same. */
function areSpatialBoxesSame(_box1, _box2) {
  return !areSpatialVectorsDifferent(_box1[0], _box2[0]) && !areSpatialVectorsDifferent(_box1[1], _box2[1]);
}

/**
 * Search defined pattern subprogram by the given id.
 * @param {number} subprogramId Subprogram Id
 * @returns {Object} Returns defined subprogram if found, otherwise returns undefined
 */
function getDefinedPatternSubprogram(subprogramId) {
  for (var i = 0; i < subprogramState.definedSubprograms.length; ++i) {
    if ((SUB_PATTERN == subprogramState.definedSubprograms[i].type) && (subprogramId == subprogramState.definedSubprograms[i].id)) {
      return subprogramState.definedSubprograms[i];
    }
  }
  return undefined;
}

/**
 * Search defined cycle subprogram pattern by the given id, initialPosition, finalPosition.
 * @param {number} subprogramId Subprogram Id
 * @param {Vector} initialPosition Initial position of the cycle
 * @param {Vector} finalPosition Final position of the cycle
 * @returns {Object} Returns defined subprogram if found, otherwise returns undefined
 */
function getDefinedCycleSubprogram(subprogramId, initialPosition, finalPosition) {
  for (var i = 0; i < subprogramState.definedSubprograms.length; ++i) {
    if ((SUB_CYCLE == subprogramState.definedSubprograms[i].type) && (subprogramId == subprogramState.definedSubprograms[i].id) &&
        !areSpatialVectorsDifferent(initialPosition, subprogramState.definedSubprograms[i].initialPosition) &&
        !areSpatialVectorsDifferent(finalPosition, subprogramState.definedSubprograms[i].finalPosition)) {
      return subprogramState.definedSubprograms[i];
    }
  }
  return undefined;
}

/**
 * Creates and returns new defined subprogram
 * @param {Section} section The section to create subprogram
 * @param {number} subprogramId Subprogram Id
 * @param {number} subprogramType Subprogram type, can be SUB_UNKNOWN, SUB_PATTERN or SUB_CYCLE
 * @param {Vector} initialPosition Initial position
 * @param {Vector} finalPosition Final position
 * @returns {Object} Returns new defined subprogram
 */
function defineNewSubprogram(section, subprogramId, subprogramType, initialPosition, finalPosition) {
  // determine if this is valid for creating a subprogram
  isValid = subprogramIsValid(section, subprogramId, subprogramType);
  var subprogram = isValid ? subprogram = ++subprogramState.lastSubprogram : undefined;
  subprogramState.definedSubprograms.push({
    type           : subprogramType,
    id             : subprogramId,
    subProgram     : subprogram,
    isValid        : isValid,
    initialPosition: initialPosition,
    finalPosition  : finalPosition
  });
  return subprogramState.definedSubprograms[subprogramState.definedSubprograms.length - 1];
}

/** Returns true if the given section is a pattern **/
function isPatternOperation(section) {
  return section.isPatterned && section.isPatterned();
}

/** Returns true if the given section is a cycle operation **/
function isCycleOperation(section, minimumCyclePoints) {
  return section.doesStrictCycle &&
  (section.getNumberOfCycles() == 1) && (section.getNumberOfCyclePoints() >= minimumCyclePoints);
}

/** Returns true if the subroutine bit flag is enabled **/
function isSubProgramEnabledFor(subroutine) {
  return subroutineBitmasks[getProperty("useSubroutines")] & subroutine;
}

/**
 * Define subprogram based on the property "useSubroutines"
 * @param {Vector} _initialPosition Initial position
 * @param {Vector} _abc Machine axis angles
 */
function subprogramDefine(_initialPosition, _abc) {
  if (isSubProgramEnabledFor(NONE)) {
    // Return early
    return;
  }

  if (subprogramState.lastSubprogram == undefined) { // initialize first subprogram number
    if (settings.subprograms.initialSubprogramNumber == undefined) {
      try {
        subprogramState.lastSubprogram = getAsInt(programName);
        subprogramState.mainProgramNumber = subprogramState.lastSubprogram; // mainProgramNumber must be a number
      } catch (e) {
        error(localize("Program name must be a number when using subprograms."));
        return;
      }
    } else {
      subprogramState.lastSubprogram = settings.subprograms.initialSubprogramNumber - 1;
      // if programName is a string set mainProgramNumber to undefined, if programName is a number set mainProgramNumber to programName
      subprogramState.mainProgramNumber = (!isNaN(programName) && !isNaN(parseInt(programName, 10))) ? getAsInt(programName) : undefined;
    }
  }

  // convert patterns into subprograms
  subprogramState.patternIsActive = false;
  if (isSubProgramEnabledFor(PATTERNS) && isPatternOperation(currentSection)) {
    var subprogramId = currentSection.getPatternId();
    var subprogramType = SUB_PATTERN;
    var subprogramDefinition = getDefinedPatternSubprogram(subprogramId);

    subprogramState.newSubprogram = !subprogramDefinition;
    if (subprogramState.newSubprogram) {
      subprogramDefinition = defineNewSubprogram(currentSection, subprogramId, subprogramType, _initialPosition, _initialPosition);
    }

    subprogramState.currentSubprogram = subprogramDefinition.subProgram;
    if (subprogramDefinition.isValid) {
      // make sure Z-position is output prior to subprogram call
      var z = zOutput.format(_initialPosition.z);
      if (!state.retractedZ && z) {
        validate(!validateLengthCompensation || state.lengthCompensationActive, "Tool length compensation is not active."); // make sure that length compensation is enabled
        var block = "";
        if (typeof gAbsIncModal != "undefined") {
          block += gAbsIncModal.format(90);
        }
        if (typeof gPlaneModal != "undefined") {
          block += gPlaneModal.format(17);
        }
        writeBlock(block);
        zOutput.reset();
        invokeOnRapid(xOutput.getCurrent(), yOutput.getCurrent(), _initialPosition.z);
      }

      // call subprogram
      subprogramCall();
      subprogramState.patternIsActive = true;

      if (subprogramState.newSubprogram) {
        subprogramStart(_initialPosition, _abc, subprogramState.incrementalSubprogram);
      } else {
        skipRemainingSection();
        setCurrentPosition(getFramePosition(currentSection.getFinalPosition()));
      }
    }
  }

  // Patterns are not used, check other cases
  if (!subprogramState.patternIsActive) {
    // Output cycle operation as subprogram
    if (isSubProgramEnabledFor(CYCLES) && isCycleOperation(currentSection, settings.subprograms.minimumCyclePoints)) {
      var finalPosition = getFramePosition(currentSection.getFinalPosition());
      var subprogramId = currentSection.getNumberOfCyclePoints();
      var subprogramType = SUB_CYCLE;
      var subprogramDefinition = getDefinedCycleSubprogram(subprogramId, _initialPosition, finalPosition);
      subprogramState.newSubprogram = !subprogramDefinition;
      if (subprogramState.newSubprogram) {
        subprogramDefinition = defineNewSubprogram(currentSection, subprogramId, subprogramType, _initialPosition, finalPosition);
      }
      subprogramState.currentSubprogram = subprogramDefinition.subProgram;
      subprogramState.cycleSubprogramIsActive = subprogramDefinition.isValid;
    }

    // Neither patterns and cycles are used, check other operations
    if (!subprogramState.cycleSubprogramIsActive && isSubProgramEnabledFor(ALLOPERATIONS)) {
      // Output all operations as subprograms
      subprogramState.currentSubprogram = ++subprogramState.lastSubprogram;
      if (subprogramState.mainProgramNumber != undefined && (subprogramState.currentSubprogram == subprogramState.mainProgramNumber)) {
        subprogramState.currentSubprogram = ++subprogramState.lastSubprogram; // avoid using main program number for current subprogram
      }
      subprogramCall();
      subprogramState.newSubprogram = true;
      subprogramStart(_initialPosition, _abc, false);
    }
  }
}

/**
 * Determine if this is valid for creating a subprogram
 * @param {Section} section The section to create subprogram
 * @param {number} subprogramId Subprogram Id
 * @param {number} subprogramType Subprogram type, can be SUB_UNKNOWN, SUB_PATTERN or SUB_CYCLE
 * @returns {boolean} If this is valid for creating a subprogram
 */
function subprogramIsValid(_section, subprogramId, subprogramType) {
  var sectionId = _section.getId();
  var numberOfSections = getNumberOfSections();
  var validSubprogram = subprogramType != SUB_CYCLE;

  var masterPosition = new Array();
  masterPosition[0] = getFramePosition(_section.getInitialPosition());
  masterPosition[1] = getFramePosition(_section.getFinalPosition());
  var tempBox = _section.getBoundingBox();
  var masterBox = new Array();
  masterBox[0] = getFramePosition(tempBox[0]);
  masterBox[1] = getFramePosition(tempBox[1]);

  var rotation = getRotation();
  var translation = getTranslation();
  subprogramState.incrementalSubprogram = undefined;

  for (var i = 0; i < numberOfSections; ++i) {
    var section = getSection(i);
    if (section.getId() != sectionId) {
      defineWorkPlane(section, false);

      // check for valid pattern
      if (subprogramType == SUB_PATTERN) {
        if (section.getPatternId() == subprogramId) {
          var patternPosition = new Array();
          patternPosition[0] = getFramePosition(section.getInitialPosition());
          patternPosition[1] = getFramePosition(section.getFinalPosition());
          tempBox = section.getBoundingBox();
          var patternBox = new Array();
          patternBox[0] = getFramePosition(tempBox[0]);
          patternBox[1] = getFramePosition(tempBox[1]);

          if (areSpatialBoxesSame(masterPosition, patternPosition) && areSpatialBoxesSame(masterBox, patternBox) && !section.isMultiAxis()) {
            subprogramState.incrementalSubprogram = subprogramState.incrementalSubprogram ? subprogramState.incrementalSubprogram : false;
          } else if (!areSpatialBoxesTranslated(masterPosition, patternPosition) || !areSpatialBoxesTranslated(masterBox, patternBox) || section.isMultiAxis() || isTCPSupportedByOperation(section)) {
            validSubprogram = false;
            break;
          } else {
            subprogramState.incrementalSubprogram = true;
          }
        }

      // check for valid cycle operation
      } else if (subprogramType == SUB_CYCLE) {
        if ((section.getNumberOfCyclePoints() == subprogramId) && (section.getNumberOfCycles() == 1)) {
          var patternInitial = getFramePosition(section.getInitialPosition());
          var patternFinal = getFramePosition(section.getFinalPosition());
          if (!areSpatialVectorsDifferent(patternInitial, masterPosition[0]) && !areSpatialVectorsDifferent(patternFinal, masterPosition[1])) {
            validSubprogram = true;
            break;
          }
        }
      }
    }
  }
  setRotation(rotation);
  setTranslation(translation);
  return (validSubprogram);
}

/**
 * Sets xyz and abc output formats to incremental or absolute type
 * @param {boolean} incremental true: Sets incremental mode, false: Sets absolute mode
 * @param {Vector} xyz Linear axis values for formating
 * @param {Vector} abc Rotary axis values for formating
*/
function setAbsIncMode(incremental, xyz, abc) {
  var outputFormats = [xOutput, yOutput, zOutput, aOutput, bOutput, cOutput];
  for (var i = 0; i < outputFormats.length; ++i) {
    outputFormats[i].setType(incremental ? TYPE_INCREMENTAL : TYPE_ABSOLUTE);
    if (typeof incPrefix != "undefined" && typeof absPrefix != "undefined") {
      outputFormats[i].setPrefix(incremental ? incPrefix[i] : absPrefix[i]);
    }
    if (i <= 2) { // xyz
      outputFormats[i].setCurrent(xyz.getCoordinate(i));
    } else { // abc
      outputFormats[i].setCurrent(abc.getCoordinate(i - 3));
    }
  }
  subprogramState.incrementalMode = incremental;
  if (typeof gAbsIncModal != "undefined") {
    if (incremental) {
      forceModals(gAbsIncModal);
    }
    writeBlock(gAbsIncModal.format(incremental ? 91 : 90));
  }
}

function setCyclePosition(_position) {
  var _spindleAxis;
  if (typeof gPlaneModal != "undefined") {
    _spindleAxis = gPlaneModal.getCurrent() == 17 ? Z : (gPlaneModal.getCurrent() == 18 ? Y : X);
  } else {
    var _spindleDirection = machineConfiguration.getSpindleAxis().getAbsolute();
    _spindleAxis = isSameDirection(_spindleDirection, new Vector(0, 0, 1)) ? Z : isSameDirection(_spindleDirection, new Vector(0, 1, 0)) ? Y : X;
  }
  switch (_spindleAxis) {
  case Z:
    zOutput.format(_position);
    break;
  case Y:
    yOutput.format(_position);
    break;
  case X:
    xOutput.format(_position);
    break;
  }
}

/**
 * Place cycle operation in subprogram
 * @param {Vector} initialPosition Initial position
 * @param {Vector} abc Machine axis angles
 * @param {boolean} incremental If the subprogram needs to go incremental mode
 */
function handleCycleSubprogram(initialPosition, abc, incremental) {
  subprogramState.cycleSubprogramIsActive &= !(cycleExpanded || isProbeOperation());
  if (subprogramState.cycleSubprogramIsActive) {
    // call subprogram
    subprogramCall();
    subprogramStart(initialPosition, abc, incremental);
  }
}

function writeSubprograms() {
  if (subprogramState.subprograms.length > 0) {
    writeln("");
    write(subprogramState.subprograms);
  }
}
// <<<<< INCLUDED FROM include_files/subprograms.cpi

// >>>>> INCLUDED FROM include_files/onRapid_fanuc.cpi
function onRapid(_x, _y, _z) {
  if (matsuuraProbeSuppressCAngleReturnRapid) {
    forceMatsuuraProbeAbsoluteRapidModals();
    forceXYZ();
    forceFeed();
    return;
  }
  var currentPosition = getCurrentPosition();
  var isPendingProbeXYMove = (matsuuraProbePendingXYReturnAfterTransfer || matsuuraProbePendingP8600ClearanceBeforeXY || matsuuraProbePendingCAngleClearanceBeforeXY) &&
    isMatsuuraRapidXYMoveFromCurrent(_x, _y, currentPosition);
  if (isPendingProbeXYMove) {
    matsuuraProbePendingXYReturnAfterTransfer = false;
    matsuuraProbePendingP8600ClearanceBeforeXY = false;
    matsuuraProbePendingCAngleClearanceBeforeXY = false;
    if (pendingRadiusCompensation >= 0) {
      error(localize("Radius compensation mode cannot be changed at rapid traversal."));
      return;
    }
    writeMatsuuraProbeFullClearanceXYMove(_x, _y, _z);
    return;
  }
  if (matsuuraProbePendingXYReturnAfterTransfer) {
    matsuuraProbePendingXYReturnAfterTransfer = false;
    if (pendingRadiusCompensation >= 0) {
      error(localize("Radius compensation mode cannot be changed at rapid traversal."));
      return;
    }
    writeMatsuuraProbeDrivingWorkOffset();
    var liftFirst = currentPosition && (xyzFormat.getResultingValue(_z) > xyzFormat.getResultingValue(currentPosition.z));
    if (liftFirst) {
      var z = zOutput.format(_z);
      if (z) {
        forceMatsuuraProbeAbsoluteRapidModals();
        writeBlock(gAbsIncModal.format(90), gMotionModal.format(0), z);
      }
      xOutput.reset();
      yOutput.reset();
      var x = xOutput.format(_x);
      var y = yOutput.format(_y);
      if (x || y) {
        forceMatsuuraProbeAbsoluteRapidModals();
        writeBlock(gAbsIncModal.format(90), gMotionModal.format(0), x, y);
      }
      if (x || y || z) {
        forceFeed();
      }
      return;
    }
    forceXYZ();
  }
  if (matsuuraProbePendingP8600ClearanceBeforeXY) {
    if (pendingRadiusCompensation >= 0) {
      error(localize("Radius compensation mode cannot be changed at rapid traversal."));
      return;
    }
    writeMatsuuraProbeDrivingWorkOffset();
    var p8600X = xOutput.format(_x);
    var p8600Y = yOutput.format(_y);
    var p8600Z = zOutput.format(_z);
    if (p8600X || p8600Y || p8600Z) {
      forceMatsuuraProbeAbsoluteRapidModals();
      writeBlock(gAbsIncModal.format(90), gMotionModal.format(0), p8600X, p8600Y, p8600Z);
      forceFeed();
    }
    return;
  }
  var x = xOutput.format(_x);
  var y = yOutput.format(_y);
  var z = zOutput.format(_z);
  if (x || y || z) {
    if (pendingRadiusCompensation >= 0) {
      error(localize("Radius compensation mode cannot be changed at rapid traversal."));
      return;
    }
    forceMotionCodeForExpandedDrilling();
    writeBlock(gMotionModal.format(0), x, y, z);
    forceFeed();
  }
}
// <<<<< INCLUDED FROM include_files/onRapid_fanuc.cpi
// >>>>> INCLUDED FROM include_files/onLinear_fanuc.cpi
function onLinear(_x, _y, _z, feed) {
  if (pendingRadiusCompensation >= 0) {
    xOutput.reset();
    yOutput.reset();
  }
  var x = xOutput.format(_x);
  var y = yOutput.format(_y);
  var z = zOutput.format(_z);
  var f = getFeed(feed);
  if (x || y || z) {
    if (pendingRadiusCompensation >= 0) {
      pendingRadiusCompensation = -1;
      var d = getMatsuuraToolDiameterOffsetWord(tool);
      writeBlock(gPlaneModal.format(17));
      switch (radiusCompensation) {
      case RADIUS_COMPENSATION_LEFT:
        writeBlock(gMotionModal.format(1), gFormat.format(41), x, y, z, d, f);
        break;
      case RADIUS_COMPENSATION_RIGHT:
        writeBlock(gMotionModal.format(1), gFormat.format(42), x, y, z, d, f);
        break;
      default:
        writeBlock(gMotionModal.format(1), gFormat.format(40), x, y, z, f);
      }
    } else {
      forceMotionCodeForExpandedDrilling();
      writeBlock(gMotionModal.format(1), x, y, z, f);
    }
  } else if (f) {
    if (getNextRecord().isMotion()) { // try not to output feed without motion
      forceFeed(); // force feed on next line
    } else {
      writeBlock(gMotionModal.format(1), f);
    }
  }
}
// <<<<< INCLUDED FROM include_files/onLinear_fanuc.cpi
// >>>>> INCLUDED FROM include_files/onRapid5D_fanuc.cpi
function onRapid5D(_x, _y, _z, _a, _b, _c) {
  if (pendingRadiusCompensation >= 0) {
    error(localize("Radius compensation mode cannot be changed at rapid traversal."));
    return;
  }
  if (!currentSection.isOptimizedForMachine()) {
    forceXYZ();
  }
  var x = xOutput.format(_x);
  var y = yOutput.format(_y);
  var z = zOutput.format(_z);
  var a = currentSection.isOptimizedForMachine() ? aOutput.format(_a) : toolVectorOutputI.format(_a);
  var b = currentSection.isOptimizedForMachine() ? bOutput.format(_b) : toolVectorOutputJ.format(_b);
  var c = currentSection.isOptimizedForMachine() ? cOutput.format(_c) : toolVectorOutputK.format(_c);
  if (matsuuraBClampedForLiveC && b) {
    error(localize("B-axis motion was detected while B is clamped for C-axis TCP machining."));
    return;
  }

  if (x || y || z || a || b || c) {
    var controlledRapidFeed = getMatsuuraTCPRapidFeed(_x, _y, _z, _a, _b, _c, a || b || c, x || y || z);
    if (controlledRapidFeed > 0) {
      var f = getFeed(controlledRapidFeed);
      writeBlock(gFeedModeModal.format(getProperty("useG95") ? 95 : 94), gMotionModal.format(1), x, y, z, a, b, c, f);
      return;
    }
    writeBlock(gMotionModal.format(0), x, y, z, a, b, c);
    forceFeed();
  }
}
// <<<<< INCLUDED FROM include_files/onRapid5D_fanuc.cpi
// >>>>> INCLUDED FROM include_files/onLinear5D_fanuc.cpi
function getMatsuuraRotaryDelta(_a, _b, _c) {
  var currentABC = getCurrentDirection();
  if (!currentABC) {
    return 0;
  }
  return Math.max(
    Math.abs(_a - currentABC.x),
    Math.abs(_b - currentABC.y),
    Math.abs(_c - currentABC.z)
  );
}

function getMatsuuraXYZChord(_x, _y, _z) {
  var currentPosition = getCurrentPosition();
  if (!currentPosition) {
    return Number.POSITIVE_INFINITY;
  }
  var dx = _x - currentPosition.x;
  var dy = _y - currentPosition.y;
  var dz = _z - currentPosition.z;
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

function getMatsuuraTCPFeed(feed, feedMode, _x, _y, _z, _a, _b, _c) {
  var maximumTCPFeed = parseFloat(getProperty("tcpMaximumCuttingFeed"));
  if (feedMode != FEED_INVERSE_TIME && isMatsuuraTCPOutputSection(currentSection) && currentSection.isMultiAxis() &&
      isFinite(maximumTCPFeed) && maximumTCPFeed > 0 && feed > maximumTCPFeed) {
    feed = maximumTCPFeed;
  }

  var xyzChord = getMatsuuraXYZChord(_x, _y, _z);
  var rotaryDelta = getMatsuuraRotaryDelta(_a, _b, _c);

  var rotaryLimiterFeed = parseFloat(getProperty("tcpRotaryLimiterFeed"));
  if (feedMode != FEED_INVERSE_TIME && isMatsuuraTCPOutputSection(currentSection) && currentSection.isMultiAxis() &&
      currentSection.isOptimizedForMachine() && isFinite(rotaryLimiterFeed) && rotaryLimiterFeed > 0 && feed > rotaryLimiterFeed) {
    var maxXYZMicrons = parseFloat(getProperty("tcpRotaryLimiterMaxXYZMicrons"));
    var minRotaryAngle = parseFloat(getProperty("tcpRotaryLimiterMinAngle"));
    var maxXYZChord = isFinite(maxXYZMicrons) && maxXYZMicrons > 0 ? toPreciseUnit(maxXYZMicrons / 1000, MM) : 0;
    minRotaryAngle = toRad(isFinite(minRotaryAngle) && minRotaryAngle > 0 ? minRotaryAngle : 1);

    if (xyzChord <= maxXYZChord && rotaryDelta >= minRotaryAngle) {
      feed = rotaryLimiterFeed;
    }
  }

  var rotaryMaxDPM = parseFloat(getProperty("tcpRotaryMaxDegreesPerMinute"));
  if (feedMode != FEED_INVERSE_TIME && isMatsuuraTCPOutputSection(currentSection) && currentSection.isMultiAxis() &&
      currentSection.isOptimizedForMachine() && isFinite(rotaryMaxDPM) && rotaryMaxDPM > 0 && xyzChord > 1e-9 && rotaryDelta > 1e-9) {
    var feedByRotaryRate = rotaryMaxDPM * xyzChord / toDeg(rotaryDelta);
    if (feedByRotaryRate > 0 && feed > feedByRotaryRate) {
      feed = feedByRotaryRate;
    }
  }
  return feed;
}

function isMatsuuraTCPRapidFeedSection(_section) {
  if (!isMatsuuraTCPOutputSection(_section)) {
    return false;
  }
  if (_section.isMultiAxis()) {
    return _section.isOptimizedForMachine();
  }
  return forceTCPForIndexedSections() && isMatsuuraIndexed3Plus2Section(_section);
}

function getMatsuuraTCPRapidFeed(_x, _y, _z, _a, _b, _c, hasRotaryOutput, hasXYZOutput) {
  var rapidFeed = parseFloat(getProperty("tcpRotaryRapidFeed"));
  if (!hasRotaryOutput || !state.tcpIsActive || !isMatsuuraTCPRapidFeedSection(currentSection) || !isFinite(rapidFeed) || rapidFeed <= 0) {
    return 0;
  }

  var feed = rapidFeed;
  var xyzChord = getMatsuuraXYZChord(_x, _y, _z);
  var rotaryDelta = getMatsuuraRotaryDelta(_a, _b, _c);
  var rotaryMaxDPM = parseFloat(getProperty("tcpRotaryMaxDegreesPerMinute"));
  if (!hasXYZOutput && isFinite(rotaryMaxDPM) && rotaryMaxDPM > 0 && feed > rotaryMaxDPM) {
    feed = rotaryMaxDPM;
  }
  if (hasXYZOutput && isFinite(rotaryMaxDPM) && rotaryMaxDPM > 0 && xyzChord > 1e-9 && rotaryDelta > 1e-9) {
    var feedByRotaryRate = rotaryMaxDPM * xyzChord / toDeg(rotaryDelta);
    if (feedByRotaryRate > 0 && feed > feedByRotaryRate) {
      feed = feedByRotaryRate;
    }
  }
  return feed;
}

function onLinear5D(_x, _y, _z, _a, _b, _c, feed, feedMode) {
  if (pendingRadiusCompensation >= 0) {
    error(localize("Radius compensation cannot be activated/deactivated for 5-axis move."));
    return;
  }
  if (!currentSection.isOptimizedForMachine()) {
    forceXYZ();
  }
  var x = xOutput.format(_x);
  var y = yOutput.format(_y);
  var z = zOutput.format(_z);
  var a = currentSection.isOptimizedForMachine() ? aOutput.format(_a) : toolVectorOutputI.format(_a);
  var b = currentSection.isOptimizedForMachine() ? bOutput.format(_b) : toolVectorOutputJ.format(_b);
  var c = currentSection.isOptimizedForMachine() ? cOutput.format(_c) : toolVectorOutputK.format(_c);
  if (matsuuraBClampedForLiveC && b) {
    error(localize("B-axis motion was detected while B is clamped for C-axis TCP machining."));
    return;
  }
  if (feedMode == FEED_INVERSE_TIME) {
    forceFeed();
  }
  var outputFeed = getMatsuuraTCPFeed(feed, feedMode, _x, _y, _z, _a, _b, _c);
  var f = feedMode == FEED_INVERSE_TIME ? inverseTimeOutput.format(feed) : getFeed(outputFeed);
  var fMode = feedMode == FEED_INVERSE_TIME ? 93 : getProperty("useG95") ? 95 : 94;

  if (x || y || z || a || b || c) {
    writeBlock(gFeedModeModal.format(fMode), gMotionModal.format(1), x, y, z, a, b, c, f);
  } else if (f) {
    if (getNextRecord().isMotion()) { // try not to output feed without motion
      forceFeed(); // force feed on next line
    } else {
      writeBlock(gFeedModeModal.format(fMode), gMotionModal.format(1), f);
    }
  }
}
// <<<<< INCLUDED FROM include_files/onLinear5D_fanuc.cpi
// >>>>> INCLUDED FROM include_files/onCircular_fanuc.cpi
function onCircular(clockwise, cx, cy, cz, x, y, z, feed) {
  if (pendingRadiusCompensation >= 0) {
    error(localize("Radius compensation cannot be activated/deactivated for a circular move."));
    return;
  }

  var start = getCurrentPosition();

  if (isFullCircle()) {
    if (getProperty("useRadius") || isHelical()) { // radius mode does not support full arcs
      linearize(tolerance);
      return;
    }
    switch (getCircularPlane()) {
    case PLANE_XY:
      writeBlock(gPlaneModal.format(17), gMotionModal.format(clockwise ? 2 : 3), iOutput.format(cx - start.x), jOutput.format(cy - start.y), getFeed(feed));
      break;
    case PLANE_ZX:
      writeBlock(gPlaneModal.format(18), gMotionModal.format(clockwise ? 2 : 3), iOutput.format(cx - start.x), kOutput.format(cz - start.z), getFeed(feed));
      break;
    case PLANE_YZ:
      writeBlock(gPlaneModal.format(19), gMotionModal.format(clockwise ? 2 : 3), jOutput.format(cy - start.y), kOutput.format(cz - start.z), getFeed(feed));
      break;
    default:
      linearize(tolerance);
    }
  } else if (!getProperty("useRadius")) {
    switch (getCircularPlane()) {
    case PLANE_XY:
      writeBlock(gPlaneModal.format(17), gMotionModal.format(clockwise ? 2 : 3), xOutput.format(x), yOutput.format(y), zOutput.format(z), iOutput.format(cx - start.x), jOutput.format(cy - start.y), getFeed(feed));
      break;
    case PLANE_ZX:
      writeBlock(gPlaneModal.format(18), gMotionModal.format(clockwise ? 2 : 3), xOutput.format(x), yOutput.format(y), zOutput.format(z), iOutput.format(cx - start.x), kOutput.format(cz - start.z), getFeed(feed));
      break;
    case PLANE_YZ:
      writeBlock(gPlaneModal.format(19), gMotionModal.format(clockwise ? 2 : 3), xOutput.format(x), yOutput.format(y), zOutput.format(z), jOutput.format(cy - start.y), kOutput.format(cz - start.z), getFeed(feed));
      break;
    default:
      if (getProperty("allow3DArcs")) {
        // make sure maximumCircularSweep is well below 360deg
        // we could use G02.4 or G03.4 - direction is calculated
        var ip = getPositionU(0.5);
        writeBlock(gMotionModal.format(clockwise ? 2.4 : 3.4), xOutput.format(ip.x), yOutput.format(ip.y), zOutput.format(ip.z), getFeed(feed));
        writeBlock(xOutput.format(x), yOutput.format(y), zOutput.format(z));
      } else {
        linearize(tolerance);
      }
    }
  } else { // use radius mode
    var r = getCircularRadius();
    if (toDeg(getCircularSweep()) > (180 + 1e-9)) {
      r = -r; // allow up to <360 deg arcs
    }
    switch (getCircularPlane()) {
    case PLANE_XY:
      writeBlock(gPlaneModal.format(17), gMotionModal.format(clockwise ? 2 : 3), xOutput.format(x), yOutput.format(y), zOutput.format(z), "R" + rFormat.format(r), getFeed(feed));
      break;
    case PLANE_ZX:
      writeBlock(gPlaneModal.format(18), gMotionModal.format(clockwise ? 2 : 3), xOutput.format(x), yOutput.format(y), zOutput.format(z), "R" + rFormat.format(r), getFeed(feed));
      break;
    case PLANE_YZ:
      writeBlock(gPlaneModal.format(19), gMotionModal.format(clockwise ? 2 : 3), xOutput.format(x), yOutput.format(y), zOutput.format(z), "R" + rFormat.format(r), getFeed(feed));
      break;
    default:
      if (getProperty("allow3DArcs")) {
        // make sure maximumCircularSweep is well below 360deg
        // we could use G02.4 or G03.4 - direction is calculated
        var ip = getPositionU(0.5);
        writeBlock(gMotionModal.format(clockwise ? 2.4 : 3.4), xOutput.format(ip.x), yOutput.format(ip.y), zOutput.format(ip.z), getFeed(feed));
        writeBlock(xOutput.format(x), yOutput.format(y), zOutput.format(z));
      } else {
        linearize(tolerance);
      }
    }
  }
}
// <<<<< INCLUDED FROM include_files/onCircular_fanuc.cpi
// >>>>> INCLUDED FROM include_files/workPlaneFunctions_fanuc.cpi
var gRotationModal = createOutputVariable({current : 69,
  onchange: function () {
    state.twpIsActive = gRotationModal.getCurrent() != 69;
    if (typeof probeVariables != "undefined") {
      probeVariables.outputRotationCodes = probeVariables.probeAngleMethod == "G68";
    }
    machineSimulation({}); // update machine simulation TWP state
  }}, gFormat);

var currentWorkPlaneABC = undefined;
function forceWorkPlane() {
  currentWorkPlaneABC = undefined;
}

function cancelWCSRotation() {
  if (typeof gRotationModal != "undefined" && gRotationModal.getCurrent() == 68) {
    cancelWorkPlane(true);
  }
}

function cancelWorkPlane(force) {
  if (typeof gRotationModal != "undefined") {
    if (force) {
      gRotationModal.reset();
    }
    var command = gRotationModal.format(69);
    if (command) {
      writeBlock(command); // cancel frame
      forceWorkPlane();
    }
  }
}

function setWorkPlane(abc) {
  if (!settings.workPlaneMethod.forceMultiAxisIndexing && is3D() && !machineConfiguration.isMultiAxisConfiguration()) {
    return; // ignore
  }
  var workplaneIsRequired = matsuuraTailstockPending || (currentWorkPlaneABC == undefined) ||
    abcFormat.areDifferent(abc.x, currentWorkPlaneABC.x) ||
    abcFormat.areDifferent(abc.y, currentWorkPlaneABC.y) ||
    abcFormat.areDifferent(abc.z, currentWorkPlaneABC.z);

  writeStartBlocks(workplaneIsRequired, function () {
    writeRetract(Z);
    if (getSetting("retract.homeXY.onIndexing", false)) {
      writeRetract(settings.retract.homeXY.onIndexing);
    }
    if ((state.lengthCompensationActive || state.tcpIsActive) && typeof disableLengthCompensation == "function") {
      disableLengthCompensation(); // cancel tool lenght compensation / TCP prior to output TWP
    }
    if (settings.workPlaneMethod.useTiltedWorkplane) {
      cancelWorkPlane(); // cancel G68.2 before G131 or M132 to prevent Alarm 5462
      if (machineConfiguration.isMultiAxisConfiguration()) {
        var machineABC = abc.isNonZero() ? (currentSection.isMultiAxis() ? getCurrentDirection() : getWorkPlaneMachineABC(currentSection, false)) : abc;
        if (matsuuraTailstockPending) {
          writeMatsuuraTailstockSecondHomeIndex(machineABC);
        } else if (matsuuraTailstockActive) {
          writeRotaryClampMCode(24); // release C only; keep B clamped at the second-home tailstock pose
          writeMatsuuraTailstockCIndex(machineABC);
        } else if (settings.workPlaneMethod.useABCPrepositioning || machineABC.isZero()) {
          if (machineABC.isZero()) {
            writeMatsuuraIndexedNeutralRotaryEntry(getCurrentDirection());
          } else {
            onCommand(COMMAND_UNLOCK_MULTI_AXIS);
            positionABC(machineABC);
          }
        } else {
          onCommand(COMMAND_UNLOCK_MULTI_AXIS);
          setCurrentABC(machineABC);
        }
      }
      if (abc.isNonZero() || !machineConfiguration.isMultiAxisConfiguration()) {
        setSmoothing(smoothing.isAllowed); // ensure high speed mode is active before G68.2
        gRotationModal.reset();
        writeBlock(
          gRotationModal.format(68.2), "X" + xyzFormat.format(currentSection.workOrigin.x), "Y" + xyzFormat.format(currentSection.workOrigin.y), "Z" + xyzFormat.format(currentSection.workOrigin.z),
          "I" + abcFormat.format(abc.x), "J" + abcFormat.format(abc.y), "K" + abcFormat.format(abc.z)
        ); // set frame
        writeBlock(gFormat.format(53.1)); // turn machine
        machineSimulation({a:getCurrentABC().x, b:getCurrentABC().y, c:getCurrentABC().z, coordinates:MACHINE, eulerAngles:abc});
      }
    } else {
      positionABC(abc, true);
    }
    if (!currentSection.isMultiAxis()) {
      onCommand(COMMAND_LOCK_MULTI_AXIS);
    }
    writeMatsuuraTailstockAdvance();
    currentWorkPlaneABC = abc;
  });
}
// <<<<< INCLUDED FROM include_files/workPlaneFunctions_fanuc.cpi
// >>>>> INCLUDED FROM include_files/writeRetract_fanuc.cpi
function writeRetract() {
  var retract = getRetractParameters.apply(this, arguments);
  if (retract && retract.words.length > 0) {
    if (typeof cancelWCSRotation == "function" && getSetting("retract.cancelRotationOnRetracting", false)) { // cancel rotation before retracting
      cancelWCSRotation();
    }
    if (typeof disableLengthCompensation == "function" && getSetting("allowCancelTCPBeforeRetracting", false) && state.tcpIsActive) {
      disableLengthCompensation(); // cancel TCP before retracting
    }
    for (var i in retract.words) {
      var words = retract.singleLine ? retract.words : retract.words[i];
      switch (retract.method) {
      case "G28":
        forceModals(gMotionModal, gAbsIncModal);
        writeBlock(gFormat.format(28), gAbsIncModal.format(91), words);
        writeBlock(gAbsIncModal.format(90));
        break;
      case "G30":
        forceModals(gMotionModal, gAbsIncModal);
        writeBlock(gFormat.format(30), gAbsIncModal.format(91), words);
        writeBlock(gAbsIncModal.format(90));
        break;
      case "G53":
        forceModals(gMotionModal);
        writeBlock(gAbsIncModal.format(90), gFormat.format(53), gMotionModal.format(0), words);
        break;
      default:
        if (typeof writeRetractCustom == "function") {
          writeRetractCustom(retract);
          return;
        } else {
          error(subst(localize("Unsupported safe position method '%1'"), retract.method));
        }
      }
      machineSimulation({
        x          : retract.singleLine || words.indexOf("X") != -1 ? retract.positions.x : undefined,
        y          : retract.singleLine || words.indexOf("Y") != -1 ? retract.positions.y : undefined,
        z          : retract.singleLine || words.indexOf("Z") != -1 ? retract.positions.z : undefined,
        coordinates: MACHINE
      });
      if (retract.singleLine) {
        break;
      }
    }
  }
}
// <<<<< INCLUDED FROM include_files/writeRetract_fanuc.cpi
// >>>>> INCLUDED FROM include_files/initialPositioning_fanuc.cpi
/**
 * Writes the initial positioning procedure for a section to get to the start position of the toolpath.
 * @param {Vector} position The initial position to move to
 * @param {boolean} isRequired true: Output full positioning, false: Output full positioning in optional state or output simple positioning only
 * @param {String} codes1 Allows to add additional code to the first positioning line
 * @param {String} codes2 Allows to add additional code to the second positioning line (if applicable)
 * @example
  var myVar1 = formatWords("T" + tool.number, currentSection.wcs);
  var myVar2 = getCoolantCodes(tool.coolant);
  writeInitialPositioning(initialPosition, isRequired, myVar1, myVar2);
*/
function writeInitialPositioning(position, isRequired, codes1, codes2, matsuuraPreviousABC) {
  var motionCode = {single:0, multi:0};
  switch (highFeedMapping) {
  case HIGH_FEED_MAP_ANY:
    motionCode = {single:1, multi:1}; // map all rapid traversals to high feed
    break;
  case HIGH_FEED_MAP_MULTI:
    motionCode = {single:0, multi:1}; // map rapid traversal along more than one axis to high feed
    break;
  }
  var feed = (highFeedMapping != HIGH_FEED_NO_MAPPING) ? getFeed(highFeedrate) : "";
  var hOffset = getMatsuuraToolLengthOffsetWord(tool);
  var additionalCodes = [formatWords(codes1), formatWords(codes2)];

  forceModals(gMotionModal);
  writeStartBlocks(isRequired, function() {
    var modalCodes = formatWords(gAbsIncModal.format(90), gPlaneModal.format(17));
    if (typeof disableLengthCompensation == "function") {
      disableLengthCompensation(!isRequired); // cancel tool length compensation prior to enabling it, required when switching G43/G43.4 modes
    }

    if (machineConfiguration.isHeadConfiguration()) { // head/head head/table kinematics
      cancelTransformation();
      var machineABC = currentSection.isMultiAxis() ? defineWorkPlane(currentSection, false) : getWorkPlaneMachineABC(currentSection, false);
      machineConfiguration.setToolLength(getSetting("workPlaneMethod.compensateToolLength", false) ? getBodyLength(currentSection.getTool()) : 0); // define the tool length for head adjustments
      var mode = currentSection.isOptimizedForMachine() ? TCP_XYZ_OPTIMIZED : TCP_XYZ;
      var globalPosition = getGlobalPosition(currentSection.getInitialPosition());
      var machinePosition = machineConfiguration.getOptimizedPosition(globalPosition, machineABC, mode, OPTIMIZE_BOTH, true);
      var prePosition = (currentSection.isOptimizedForMachine() || currentSection.isMultiAxis()) ? position :
        (settings.workPlaneMethod.useTiltedWorkplane && !tcp.isSupportedByMachine) ? machinePosition : globalPosition;

      cancelWorkPlane();
      positionABC(machineABC);
      if ((getSetting("workPlaneMethod.useTiltedWorkplane", false) && tcp.isSupportedByMachine && getCurrentDirection().isNonZero()) || tcp.isSupportedByOperation) {
        writeBlock(getOffsetCode(true), hOffset); // force TCP for prepositioning although the operation may not require it
      }
      writeBlock(modalCodes, gMotionModal.format(motionCode.multi), xOutput.format(prePosition.x), yOutput.format(prePosition.y), feed, additionalCodes[0]);
      machineSimulation({x:prePosition.x, y:prePosition.y});
      if (currentSection.isMultiAxis() || getSetting("headPositioningMethod", 0) == 1) {
        var lengthComp = state.lengthCompensationActive ? {code:undefined, hOffset:undefined} : {code:getOffsetCode(), hOffset:hOffset};
        writeBlock(modalCodes, gMotionModal.format(motionCode.single), lengthComp.code, zOutput.format(prePosition.z), lengthComp.hOffset, additionalCodes[1]);
        machineSimulation({z:prePosition.z});
      }

      if (!currentSection.isMultiAxis()) {
        if (state.tcpIsActive && !tcp.isSupportedByOperation && typeof disableLengthCompensation == "function") {
          disableLengthCompensation();
        }
        if (getSetting("workPlaneMethod.useTiltedWorkplane", false) && getCurrentDirection().isNonZero()) {
          var saveRetractedState = [state.retractedX, state.retractedY, state.retractedZ];
          state.retractedX = state.retractedY = state.retractedZ = true; // set retracted states to true to avoid retraction
          defineWorkPlane(currentSection, true); // apply workplane for the operation if TWP is supported
          [state.retractedX, state.retractedY, state.retractedZ] = saveRetractedState; // restore retracted states
        }
        if (!state.lengthCompensationActive) {
          if (state.twpIsActive) {
            forceXYZ();
          }
          if (getSetting("headPositioningMethod", 0) == 1) {
            writeBlock(modalCodes, gMotionModal.format(motionCode.multi), xOutput.format(position.x), yOutput.format(position.y));
            machineSimulation({x:position.x, y:position.y});
            writeBlock(modalCodes, gMotionModal.format(motionCode.single), getOffsetCode(), zOutput.format(position.z), hOffset);
            machineSimulation({z:position.z});
          } else {
            writeBlock(modalCodes, getOffsetCode(), gMotionModal.format(motionCode.single), xOutput.format(position.x), yOutput.format(position.y), zOutput.format(position.z), hOffset);
            machineSimulation({x:position.x, y:position.y, z:position.z});
          }
        }
      }
      forceFeed();
    } else {
      // multi axis prepositioning with TWP
      if (useTWPForMultiAxisTCPPrepositioning() && currentSection.isMultiAxis() && getSetting("workPlaneMethod.prepositionWithTWP", true) && getSetting("workPlaneMethod.useTiltedWorkplane", false) &&
        tcp.isSupportedByOperation && getCurrentDirection().isNonZero()) {
        var W = machineConfiguration.isMultiAxisConfiguration() ? machineConfiguration.getOrientation(getCurrentDirection()) :
          Matrix.getOrientationFromDirection(getCurrentDirection());
        var prePosition = W.getTransposed().multiply(position);
        var angles = W.getEuler2(settings.workPlaneMethod.eulerConvention);
        setWorkPlane(angles);
        writeBlock(modalCodes, gMotionModal.format(motionCode.multi), xOutput.format(prePosition.x), yOutput.format(prePosition.y), feed, additionalCodes[0]);
        machineSimulation({x:prePosition.x, y:prePosition.y});
        cancelWorkPlane();
        writeBlock(getOffsetCode(), hOffset, additionalCodes[1]); // omit Z-axis output is desired
        forceAny(); // required to output XYZ coordinates in the following line
      } else if (tcp.isSupportedByOperation) {
        // Accepted Matsuura table/table TCP entry, matching the verified 2015 proof:
        // B0 C0 -> G43.4 H -> first TCP X/Y -> safe Z -> first B/C under active TCP.
        writeMatsuuraTCPNeutralRotaryEntry(matsuuraPreviousABC);
        writeBlock(modalCodes, getOffsetCode(), hOffset, additionalCodes[1]);
        forceXYZ();
        writeBlock(modalCodes, gMotionModal.format(motionCode.multi), xOutput.format(position.x), yOutput.format(position.y), feed, additionalCodes[0]);
        machineSimulation({x:position.x, y:position.y});
        writeBlock(gMotionModal.format(motionCode.single), zOutput.format(position.z));
        machineSimulation({x:position.x, y:position.y, z:position.z});
        var tcpEntryABC = getTCPEntryABCForSection(currentSection);
        forceABC();
        gMotionModal.reset();
        var a = aOutput.format(tcpEntryABC.x);
        var b = bOutput.format(tcpEntryABC.y);
        var c = cOutput.format(tcpEntryABC.z);
        if (a || b || c) {
          var controlledEntryFeed = getMatsuuraTCPRapidFeed(position.x, position.y, position.z, tcpEntryABC.x, tcpEntryABC.y, tcpEntryABC.z, a || b || c, false);
          if (controlledEntryFeed > 0) {
            writeBlock(gFeedModeModal.format(getProperty("useG95") ? 95 : 94), gMotionModal.format(1), a, b, c, getFeed(controlledEntryFeed));
          } else {
            writeBlock(gMotionModal.format(motionCode.multi), a, b, c);
          }
          setCurrentABC(tcpEntryABC);
          machineSimulation({a:tcpEntryABC.x, b:tcpEntryABC.y, c:tcpEntryABC.z, coordinates:MACHINE});
        }
        if (isCAxisOnlyTCPSection(currentSection)) {
          clampBAndReleaseCForLiveC();
        } else if (!currentSection.isMultiAxis() && tcpEntryABC.isNonZero()) {
          onCommand(COMMAND_LOCK_MULTI_AXIS);
        }
      } else {
        writeBlock(modalCodes, gMotionModal.format(motionCode.multi), xOutput.format(position.x), yOutput.format(position.y), feed, additionalCodes[0]);
        machineSimulation({x:position.x, y:position.y});
        writeBlock(gMotionModal.format(motionCode.single), getOffsetCode(), zOutput.format(position.z), hOffset, additionalCodes[1]);
        machineSimulation(tcp.isSupportedByOperation ? {x:position.x, y:position.y, z:position.z} : {z:position.z});
      }
    }
    forceModals(gMotionModal);
    if (isRequired) {
      additionalCodes = []; // clear additionalCodes buffer
    }
  });

  validate(!validateLengthCompensation || state.lengthCompensationActive, "Tool length compensation is not active."); // make sure that lenght compensation is enabled
  if (!isRequired) { // simple positioning
    var modalCodes = formatWords(gAbsIncModal.format(90), gPlaneModal.format(17));
    forceXYZ();
    if (!state.retractedZ && xyzFormat.getResultingValue(getCurrentPosition().z) < xyzFormat.getResultingValue(position.z)) {
      writeBlock(modalCodes, gMotionModal.format(motionCode.single), zOutput.format(position.z), feed);
      machineSimulation({z:position.z});
    }
    writeBlock(modalCodes, gMotionModal.format(motionCode.multi), xOutput.format(position.x), yOutput.format(position.y), feed, additionalCodes);
    machineSimulation({x:position.x, y:position.y});
  }
  if (machineConfiguration.isMultiAxisConfiguration() && !currentSection.isMultiAxis()) {
    onCommand(COMMAND_LOCK_MULTI_AXIS);
  }
}

Matrix.getOrientationFromDirection = function (ijk) {
  var forward = ijk;
  var unitZ = new Vector(0, 0, 1);
  var W;
  if (Math.abs(Vector.dot(forward, unitZ)) < 0.5) {
    var imX = Vector.cross(forward, unitZ).getNormalized();
    W = new Matrix(imX, Vector.cross(forward, imX), forward);
  } else {
    var imX = Vector.cross(new Vector(0, 1, 0), forward).getNormalized();
    W = new Matrix(imX, Vector.cross(forward, imX), forward);
  }
  return W;
};
// <<<<< INCLUDED FROM include_files/initialPositioning_fanuc.cpi
// >>>>> INCLUDED FROM include_files/getOffsetCode_fanuc.cpi
var toolLengthCompOutput = createOutputVariable({control : CONTROL_FORCE,
  onchange: function() {
    state.tcpIsActive = toolLengthCompOutput.getCurrent() == 43.4 || toolLengthCompOutput.getCurrent() == 43.5;
    state.lengthCompensationActive = toolLengthCompOutput.getCurrent() != 49;
    machineSimulation({}); // update machine simulation TCP state
  }
}, gFormat);

function getOffsetCode(forceTCP) {
  if (!getSetting("outputToolLengthCompensation", true) && toolLengthCompOutput.isEnabled()) {
    state.lengthCompensationActive = true; // always assume that length compensation is active
    toolLengthCompOutput.disable();
  }
  var offsetCode = 43;
  if (tcp.isSupportedByOperation || forceTCP) {
    offsetCode = machineConfiguration.isMultiAxisConfiguration() ? 43.4 : 43.5;
  }
  return toolLengthCompOutput.format(offsetCode);
}
// <<<<< INCLUDED FROM include_files/getOffsetCode_fanuc.cpi
// >>>>> INCLUDED FROM include_files/disableLengthCompensation_fanuc.cpi
function disableLengthCompensation(force, allowAtClearance) {
  if (state.lengthCompensationActive || force) {
    if (force) {
      toolLengthCompOutput.reset();
    }
    if (!allowAtClearance && !getSetting("allowCancelTCPBeforeRetracting", false)) {
      validate(state.retractedZ, "Cannot cancel tool length compensation if the machine is not fully retracted.");
    }
    writeBlock(toolLengthCompOutput.format(49));
  }
}
// <<<<< INCLUDED FROM include_files/disableLengthCompensation_fanuc.cpi
// >>>>> INCLUDED FROM include_files/getProgramNumber_fanuc.cpi
function getProgramNumber() {
  if (typeof oFormat != "undefined" && getProperty("o8")) {
    oFormat.setMinDigitsLeft(8);
  }
  var minimumProgramNumber = getSetting("programNumber.min", 1);
  var maximumProgramNumber = getSetting("programNumber.max", getProperty("o8") ? 99999999 : 9999);
  var reservedProgramNumbers = getSetting("programNumber.reserved", [8000, 9999]);
  if (programName) {
    var _programNumber;
    try {
      _programNumber = getAsInt(programName);
    } catch (e) {
      error(localize("Program name must be a number."));
    }
    if (!((_programNumber >= minimumProgramNumber) && (_programNumber <= maximumProgramNumber))) {
      error(subst(localize("Program number '%1' is out of range. Please enter a program number between '%2' and '%3'."), _programNumber, minimumProgramNumber, maximumProgramNumber));
    }
    if ((_programNumber >= reservedProgramNumbers[0]) && (_programNumber <= reservedProgramNumbers[1])) {
      warning(subst(localize("Program number '%1' is potentially reserved by the machine tool builder. Reserved range is '%2' to '%3'."), _programNumber, reservedProgramNumbers[0], reservedProgramNumbers[1]));
    }
  } else {
    error(localize("Program name has not been specified."));
  }
  return _programNumber;
}
// <<<<< INCLUDED FROM include_files/getProgramNumber_fanuc.cpi
// >>>>> INCLUDED FROM include_files/rewind.cpi
function onMoveToSafeRetractPosition() {
  if (!getSetting("allowCancelTCPBeforeRetracting", false)) {
    writeRetract(Z);
  }
  if (state.tcpIsActive) { // cancel TCP so that tool doesn't follow rotaries
    if (typeof setTCP == "function") {
      setTCP(false);
    } else {
      disableLengthCompensation(false);
    }
  }
  writeRetract(Z);
  if (getSetting("retract.homeXY.onIndexing", false)) {
    writeRetract(settings.retract.homeXY.onIndexing);
  }
}

/** Rotate axes to new position above reentry position */
function onRotateAxes(_x, _y, _z, _a, _b, _c) {
  // position rotary axes
  xOutput.disable();
  yOutput.disable();
  zOutput.disable();
  if (typeof unwindABC == "function") {
    unwindABC(new Vector(_a, _b, _c), false);
  }
  onRapid5D(_x, _y, _z, _a, _b, _c);
  setCurrentABC(new Vector(_a, _b, _c));
  machineSimulation({a:_a, b:_b, c:_c, coordinates:MACHINE});
  xOutput.enable();
  yOutput.enable();
  zOutput.enable();
  forceXYZ();
}

/** Return from safe position after indexing rotaries. */
function onReturnFromSafeRetractPosition(_x, _y, _z) {
  if (!machineConfiguration.isHeadConfiguration()) {
    writeInitialPositioning(new Vector(_x, _y, _z), true);
    if (highFeedMapping != HIGH_FEED_NO_MAPPING) {
      onLinear5D(_x, _y, _z, getCurrentDirection().x, getCurrentDirection().y, getCurrentDirection().z, highFeedrate);
    } else {
      onRapid5D(_x, _y, _z, getCurrentDirection().x, getCurrentDirection().y, getCurrentDirection().z);
    }
    machineSimulation({x:_x, y:_y, z:_z, a:getCurrentDirection().x, b:getCurrentDirection().y, c:getCurrentDirection().z});
  } else {
    if (tcp.isSupportedByOperation) {
      if (typeof setTCP == "function") {
        setTCP(true);
      } else {
        writeBlock(getOffsetCode(), getMatsuuraToolLengthOffsetWord(tool));
      }
    }
    forceXYZ();
    xOutput.reset();
    yOutput.reset();
    zOutput.disable();
    if (highFeedMapping != HIGH_FEED_NO_MAPPING) {
      onLinear(_x, _y, _z, highFeedrate);
    } else {
      onRapid(_x, _y, _z);
    }
    machineSimulation({x:_x, y:_y});
    zOutput.enable();
    invokeOnRapid(_x, _y, _z);
  }
}
// <<<<< INCLUDED FROM include_files/rewind.cpi
// >>>>> INCLUDED FROM include_files/commonInspectionFunctions_fanuc.cpi
var macroFormat = createFormat({prefix:(typeof inspectionVariables == "undefined" ? "#" : inspectionVariables.localVariablePrefix), decimals:0});
var macroRoundingFormat = (unit == MM) ? "[53]" : "[44]";
var isDPRNTopen = false;

var WARNING_OUTDATED = 0;
var toolpathIdFormat = createFormat({decimals:5, type:FORMAT_REAL});
var patternInstances = new Array();
var initializePatternInstances = true; // initialize patternInstances array the first time inspectionGetToolpathId is called
function inspectionGetToolpathId(section) {
  if (initializePatternInstances) {
    for (var i = 0; i < getNumberOfSections(); ++i) {
      var _section = getSection(i);
      if (_section.getInternalPatternId) {
        var sectionId = _section.getId();
        var patternId = _section.getInternalPatternId();
        var isPatterned = _section.isPatterned && _section.isPatterned();
        var isMirrored = patternId != _section.getPatternId();
        if (isPatterned || isMirrored) {
          var isKnownPatternId = false;
          for (var j = 0; j < patternInstances.length; j++) {
            if (patternId == patternInstances[j].patternId) {
              patternInstances[j].patternIndex++;
              patternInstances[j].sections.push(sectionId);
              isKnownPatternId = true;
              break;
            }
          }
          if (!isKnownPatternId) {
            patternInstances.push({patternId:patternId, patternIndex:1, sections:[sectionId]});
          }
        }
      }
    }
    initializePatternInstances = false;
  }

  var _operationId = section.getParameter("autodeskcam:operation-id", "");
  var key = -1;
  for (k in patternInstances) {
    if (patternInstances[k].patternId == _operationId) {
      key = k;
      break;
    }
  }
  var _patternId = (key > -1) ? patternInstances[key].sections.indexOf(section.getId()) + 1 : 0;
  var _cycleId = cycle && ("cycleID" in cycle) ? cycle.cycleID : section.getParameter("cycleID", 0);
  if (isProbeOperation(section) && _cycleId == 0 && getGlobalParameter("product-id").toLowerCase().indexOf("fusion") > -1) {
    // we expect the cycleID to be non zero always for macro probing toolpaths, Fusion only
    warningOnce(localize("Outdated macro probing operations detected. Please regenerate all macro probing operations."), WARNING_OUTDATED);
  }
  if (_patternId > 99) {
    error(subst(localize("The maximum number of pattern instances is limited to 99" + EOL +
      "You need to split operation '%1' into separate pattern groups."
    ), section.getParameter("operation-comment", "")));
  }
  if (_cycleId > 99) {
    error(subst(localize("The maximum number of probing cycles is limited to 99" + EOL +
      "You need to split operation '%1' to multiple operations with less than 100 cycles in each operation."
    ), section.getParameter("operation-comment", "")));
  }
  return toolpathIdFormat.format(_operationId + (_cycleId * 0.01) + (_patternId * 0.0001) + 0.00001);
}

var localVariableStart = 19;
var localVariable = [
  macroFormat.format(localVariableStart + 1),
  macroFormat.format(localVariableStart + 2),
  macroFormat.format(localVariableStart + 3),
  macroFormat.format(localVariableStart + 4),
  macroFormat.format(localVariableStart + 5),
  macroFormat.format(localVariableStart + 6)
];

function defineLocalVariable(indx, value) {
  writeln(localVariable[indx - 1] + " = " + value);
}

function formatLocalVariable(prefix, indx, rnd) {
  return prefix + localVariable[indx - 1] + rnd;
}

function inspectionCreateResultsFileHeader() {
  if (isDPRNTopen) {
    if (!getProperty("singleResultsFile")) {
      writeln("DPRNT[END]");
      writeBlock("PCLOS");
      isDPRNTopen = false;
    }
  }

  if (isProbeOperation() && !printProbeResults()) {
    return; // if print results is not desired by probe/ probeWCS
  }

  if (!isDPRNTopen) {
    writeBlock("PCLOS");
    writeBlock("POPEN");
    // check for existence of none alphanumeric characters but not spaces
    var resFile;
    if (getProperty("singleResultsFile")) {
      resFile = getParameter("job-description") + "-RESULTS";
    } else {
      resFile = getParameter("operation-comment") + "-RESULTS";
    }
    resFile = resFile.replace(/:/g, "-");
    resFile = resFile.replace(/[^a-zA-Z0-9 -]/g, "");
    resFile = resFile.replace(/\s/g, "-");
    resFile = resFile.toUpperCase();
    writeln("DPRNT[START]");
    writeln("DPRNT[RESULTSFILE*" + resFile + "]");
    if (hasGlobalParameter("document-id")) {
      writeln("DPRNT[DOCUMENTID*" + getGlobalParameter("document-id").toUpperCase() + "]");
    }
    if (hasGlobalParameter("model-version")) {
      writeln("DPRNT[MODELVERSION*" + getGlobalParameter("model-version").toUpperCase() + "]");
    }
  }
  if (isProbeOperation() && printProbeResults()) {
    isDPRNTopen = true;
  }
}

function getPointNumber() {
  if (typeof inspectionWriteVariables == "function") {
    return (inspectionVariables.pointNumber);
  } else {
    return ("#122[60]");
  }
}

function inspectionWriteCADTransform() {
  var cadOrigin = currentSection.getModelOrigin();
  var cadWorkPlane = currentSection.getModelPlane().getTransposed();
  var cadEuler = cadWorkPlane.getEuler2(EULER_XYZ_S);
  defineLocalVariable(1, abcFormat.format(cadEuler.x));
  defineLocalVariable(2, abcFormat.format(cadEuler.y));
  defineLocalVariable(3, abcFormat.format(cadEuler.z));
  defineLocalVariable(4, xyzFormat.format(-cadOrigin.x));
  defineLocalVariable(5, xyzFormat.format(-cadOrigin.y));
  defineLocalVariable(6, xyzFormat.format(-cadOrigin.z));
  writeln(
    "DPRNT[G331" +
    "*N" + getPointNumber() +
    formatLocalVariable("*A", 1, macroRoundingFormat) +
    formatLocalVariable("*B", 2, macroRoundingFormat) +
    formatLocalVariable("*C", 3, macroRoundingFormat) +
    formatLocalVariable("*X", 4, macroRoundingFormat) +
    formatLocalVariable("*Y", 5, macroRoundingFormat) +
    formatLocalVariable("*Z", 6, macroRoundingFormat) +
    "]"
  );
}

function inspectionWriteWorkplaneTransform() {
  var orientation = machineConfiguration.isMultiAxisConfiguration() ? machineConfiguration.getOrientation(getCurrentDirection()) : currentSection.workPlane;
  var abc = orientation.getEuler2(EULER_XYZ_S);
  if (getProperty("useLiveConnection")) {
    liveConnectorInterface("WORKPLANE");
    writeln(inspectionVariables.liveConnectionWPA + " = " + abcFormat.format(abc.x));
    writeln(inspectionVariables.liveConnectionWPB + " = " + abcFormat.format(abc.y));
    writeln(inspectionVariables.liveConnectionWPC + " = " + abcFormat.format(abc.z));
    writeBlock("IF [" + inspectionVariables.workplaneStartAddress, "NE -1] GOTO" + skipNLines(2));
    writeBlock(inspectionVariables.workplaneStartAddress, "=", inspectionGetToolpathId(currentSection));
    writeBlock(" "); // do not remove, required for GOTO functionality
  }

  defineLocalVariable(1, abcFormat.format(abc.x));
  defineLocalVariable(2, abcFormat.format(abc.y));
  defineLocalVariable(3, abcFormat.format(abc.z));
  writeln("DPRNT[G330" +
    "*N" + getPointNumber() +
    formatLocalVariable("*A", 1, macroRoundingFormat) +
    formatLocalVariable("*B", 2, macroRoundingFormat) +
    formatLocalVariable("*C", 3, macroRoundingFormat) +
    "*X0*Y0*Z0*I0*R0]"
  );
}

function writeProbingToolpathInformation(cycleDepth) {
  writeln("DPRNT[TOOLPATHID*" + inspectionGetToolpathId(currentSection) + "]");
  if (isInspectionOperation()) {
    writeln("DPRNT[TOOLPATH*" + getParameter("operation-comment").toUpperCase().replace(/[()]/g, "") + "]");
  } else {
    defineLocalVariable(2, xyzFormat.format(cycleDepth));
    writeln(formatLocalVariable("DPRNT[CYCLEDEPTH*", 2, macroRoundingFormat + "]"));
  }
}
// <<<<< INCLUDED FROM include_files/commonInspectionFunctions_fanuc.cpi
// >>>>> INCLUDED FROM include_files/getProbingArguments_renishaw.cpi
function getProbingArguments(cycle, updateWCS) {
  var outputWCSCode = updateWCS && currentSection.strategy == "probe";
  if (outputWCSCode) {
    var maximumWcsNumber = 0;
    for (var i in wcsDefinitions.wcs) {
      maximumWcsNumber = Math.max(maximumWcsNumber, wcsDefinitions.wcs[i].range[1]);
    }
    maximumWcsNumber = probeExtWCSFormat.getResultingValue(maximumWcsNumber);
    var resultingWcsNumber = probeExtWCSFormat.getResultingValue(currentSection.probeWorkOffset - 6);
    validate(resultingWcsNumber <= maximumWcsNumber, subst("Probe work offset %1 is out of range, maximum value is %2.", resultingWcsNumber, maximumWcsNumber));
    var probeOutputWorkOffset = currentSection.probeWorkOffset > 6 ? probeExtWCSFormat.format(currentSection.probeWorkOffset - 6) : probeWCSFormat.format(currentSection.probeWorkOffset);

    var nextWorkOffset = hasNextSection() ? getNextSection().workOffset == 0 ? 1 : getNextSection().workOffset : -1;
    if (currentSection.probeWorkOffset == nextWorkOffset) {
      currentWorkOffset = undefined;
    }
  }
  return [
    (cycle.angleAskewAction == "stop-message" ? "B" + xyzFormat.format(cycle.toleranceAngle ? cycle.toleranceAngle : 0) : undefined),
    ((cycle.updateToolWear && cycle.toolWearErrorCorrection < 100) ? "F" + xyzFormat.format(cycle.toolWearErrorCorrection ? cycle.toolWearErrorCorrection / 100 : 100) : undefined),
    (cycle.wrongSizeAction == "stop-message" ? "H" + xyzFormat.format(cycle.toleranceSize ? cycle.toleranceSize : 0) : undefined),
    (cycle.outOfPositionAction == "stop-message" ? "M" + xyzFormat.format(cycle.tolerancePosition ? cycle.tolerancePosition : 0) : undefined),
    ((cycle.updateToolWear && cycleType == "probing-z") ? "T" + xyzFormat.format(cycle.toolLengthOffset) : undefined),
    ((cycle.updateToolWear && cycleType !== "probing-z") ? "T" + xyzFormat.format(cycle.toolDiameterOffset) : undefined),
    (cycle.updateToolWear ? "V" + xyzFormat.format(cycle.toolWearUpdateThreshold ? cycle.toolWearUpdateThreshold : 0) : undefined),
    (cycle.printResults ? "W" + xyzFormat.format(1 + cycle.incrementComponent) : undefined), // 1 for advance feature, 2 for reset feature count and advance component number. first reported result in a program should use W2.
    conditional(outputWCSCode, probeOutputWorkOffset)
  ];
}
// <<<<< INCLUDED FROM include_files/getProbingArguments_renishaw.cpi
// >>>>> INCLUDED FROM include_files/setProbeAngle_fanuc.cpi
function setProbeAngle() {
  if (probeVariables.outputRotationCodes) {
    validate(settings.probing.probeAngleVariables, localize("Setting 'probing.probeAngleVariables' is required for angular probing."));
    var probeAngleVariables = settings.probing.probeAngleVariables;
    var px = probeAngleVariables.x;
    var py = probeAngleVariables.y;
    var pz = probeAngleVariables.z;
    var pi = probeAngleVariables.i;
    var pj = probeAngleVariables.j;
    var pk = probeAngleVariables.k;
    var pr = probeAngleVariables.r;
    var baseParamG54x4 = probeAngleVariables.baseParamG54x4;
    var baseParamAxisRot = probeAngleVariables.baseParamAxisRot;
    var probeOutputWorkOffset = currentSection.probeWorkOffset;

    validate(probeOutputWorkOffset <= 6, "Angular Probing only supports work offsets 1-6.");
    if (probeVariables.probeAngleMethod == "G68" && (Vector.diff(currentSection.getGlobalInitialToolAxis(), new Vector(0, 0, 1)).length > 1e-4)) {
      error(localize("You cannot use multi axis toolpaths while G68 Rotation is in effect."));
    }
    var validateWorkOffset = false;
    switch (probeVariables.probeAngleMethod) {
    case "G54.4":
      var param = baseParamG54x4 + (probeOutputWorkOffset * 10);
      writeBlock("#" + param + "=" + px);
      writeBlock("#" + (param + 1) + "=" + py);
      writeBlock("#" + (param + 5) + "=" + pr);
      writeBlock(gFormat.format(54.4), "P" + probeOutputWorkOffset);
      break;
    case "G68":
      gRotationModal.reset();
      gAbsIncModal.reset();
      var xy = probeVariables.compensationXY || formatWords(formatCompensationParameter("X", px), formatCompensationParameter("Y", py));
      writeBlock(
        gRotationModal.format(68), gAbsIncModal.format(90),
        xy,
        formatCompensationParameter("Z", pz),
        formatCompensationParameter("I", pi),
        formatCompensationParameter("J", pj),
        formatCompensationParameter("K", pk),
        formatCompensationParameter("R", pr)
      );
      validateWorkOffset = true;
      break;
    case "AXIS_ROT":
      var param = baseParamAxisRot + probeOutputWorkOffset * 20 + probeVariables.rotaryTableAxis + 4;
      writeBlock("#" + param + " = " + "[#" + param + " + " + pr + "]");
      forceWorkPlane(); // force workplane to rotate ABC in order to apply rotation offsets
      currentWorkOffset = undefined; // force WCS output to make use of updated parameters
      validateWorkOffset = true;
      break;
    default:
      error(localize("Angular Probing is not supported for this machine configuration."));
      return;
    }
    if (validateWorkOffset) {
      for (var i = currentSection.getId(); i < getNumberOfSections(); ++i) {
        if (getSection(i).workOffset != currentSection.workOffset) {
          error(localize("WCS offset cannot change while using angle rotation compensation."));
          return;
        }
      }
    }
    probeVariables.outputRotationCodes = false;
  }
}

function formatCompensationParameter(label, value) {
  return typeof value == "string" ? label + "[" + value + "]" : typeof value == "number" ? label + xyzFormat.format(value) : "";
}
// <<<<< INCLUDED FROM include_files/setProbeAngle_fanuc.cpi
// >>>>> INCLUDED FROM include_files/setProbeAngleMethod.cpi
function setProbeAngleMethod() {
  var axisRotIsSupported = false;
  var axes = [machineConfiguration.getAxisU(), machineConfiguration.getAxisV(), machineConfiguration.getAxisW()];
  for (var i = 0; i < axes.length; ++i) {
    if (axes[i].isEnabled() && isSameDirection((axes[i].getAxis()).getAbsolute(), new Vector(0, 0, 1)) && axes[i].isTable()) {
      axisRotIsSupported = true;
      if (settings.probing.probeAngleVariables.method == 0) { // Fanuc
        validate(i < 2, localize("Rotary table axis is invalid."));
        probeVariables.rotaryTableAxis = i;
      } else { // Haas
        probeVariables.rotaryTableAxis = axes[i].getCoordinate();
      }
      break;
    }
  }
  if (settings.probing.probeAngleMethod == undefined) {
    probeVariables.probeAngleMethod = axisRotIsSupported ? "AXIS_ROT" : getProperty("useG54x4") ? "G54.4" : "G68"; // automatic selection
  } else {
    probeVariables.probeAngleMethod = settings.probing.probeAngleMethod; // use probeAngleMethod from settings
    if (probeVariables.probeAngleMethod == "AXIS_ROT" && !axisRotIsSupported) {
      error(localize("Setting probeAngleMethod 'AXIS_ROT' is not supported on this machine."));
    }
  }
  probeVariables.outputRotationCodes = true;
}
// <<<<< INCLUDED FROM include_files/setProbeAngleMethod.cpi
