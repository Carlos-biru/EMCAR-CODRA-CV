﻿using System;
using System.Collections;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using log4net;
using UniversalRobotsConnect.Types;

[assembly: log4net.Config.XmlConfigurator(Watch = true)]

namespace UniversalRobotsConnect
{

    #region enums

    public enum ConnectionState : int
    {
        Error = 0,
        Disconnected = 1,
        Connected = 2,
        Paused = 3,
        Started = 4
    }

    public enum RobotMode : uint
    {
        DISCONNECTED = 0,
        CONFIRM_SAFETY = 1,
        BOOTING = 2,
        POWER_OFF = 3,
        POWER_ON = 4,
        IDLE = 5,
        BACKDRIVE = 6,
        RUNNING = 7,
        UPDATING_FIRMWARE = 8
    }

    public enum SafetyMode : uint
    {
        Normal = 1,
        Reduced = 2,
        ProtectiveStop = 3,
        Recovery = 4,
        SafeguardStop = 5,
        SystemEmergencyStop = 6,
        RobotEmergencyStop = 7,
        Violation = 8,
        Fault = 9
    }
    
    /// <summary>
    /// The State of a program running on the Robot - UnInitialized until the first program is send to robot, then alternating between Idle and Running depending.
    /// </summary>
    public enum RuntimeState : uint
    {
        UnInitialized = 0,
        Idle = 1,
        Running = 2
    }

    public enum JointMode : int
    {
        ShuttingDown = 236,
        PartDCalibration = 237,
        BackDrive = 238,
        PowerOff = 239,
        NotResponding = 245,
        MotorInitialization = 246,
        Booting = 247,
        PartDCalibrationError = 248,
        Bootloader = 249,
        Calibration = 250,
        Fault = 252,
        Running = 253,
        Idle = 255
    }

    #endregion

    public class RobotModel
    {

        private static readonly ILog log = LogManager.GetLogger(System.Reflection.MethodBase.GetCurrentMethod().DeclaringType);

        #region BackingFields

        //private bool _digitalOutputBit0;
        //private bool _digitalOutputBit1;
        //private bool _digitalOutputBit2;
        //private bool _digitalOutputBit3;
        //private bool _digitalOutputBit4;
        //private bool _digitalOutputBit5;
        //private bool _digitalOutputBit6;
        //private bool _digitalOutputBit7;
        private double[] _actualTCPPose;
        private RobotMode _robotMode;
        private SafetyMode _safetyMode;
        private int _rtdeProtocolVersion;
        private double[] _targetQ;
        private double _vector6DPrecision = 0.00001;
        private double[] _targetQD;
        private double[] _targetQDD;
        private double[] _targetCurrent;
        private double[] _targetMoment;
        private double[] _actualQ;
        private double[] _actualQD;
        private double[] _actualCurrent;
        //private bool _digitalInputBit0;
        //private bool _digitalInputBit1;
        //private bool _digitalInputBit2;
        //private bool _digitalInputBit3;
        //private bool _digitalInputBit4;
        //private bool _digitalInputBit5;
        //private bool _digitalInputBit6;
        //private bool _digitalInputBit7;
        private double[] _targetTCPPose;
        private RuntimeState _runtimeState;
        //private bool _robotStatusPowerOn;
        private SafetyStatus _safetyStatus = new SafetyStatus();
        private RobotStatus _robotStatus = new RobotStatus();
        private double _robotTimeStamp;
        private double[] _forceTorque;
        private BitArray _digitalOutputBits;
        private BitArray _digitalInputBits;
        private BitArray _outputBitRegisters = new BitArray(64);

        #endregion

        public string Password { get; set; }

        public IPAddress IpAddress { get; set; }

        public double RobotTimestamp
        {
            get { return _robotTimeStamp; }
            set
            {
                //log.Info($"{RobotTimestamp} , RobotTimestamp");
                //double delta = value - _robotTimeStamp;
                //if (delta > 0.0081)
                //{
                //    log.Error($"Time since last RTDE timestamp: {delta}");
                //}
                _robotTimeStamp = value;
            }
        }

        public ConnectionState RTDEConnectionState { get; set; }

        /// <summary>
        /// Flag used when program using UR-Script and UR-ScriptEXT needs to shut down before completed
        /// This can be in seperate threads - set this flag when need to stop and listen in all threads
        /// </summary>
        public bool StopRunningFlag { get; set; } = false;
        
        #region Digital Input Bits

        public bool GetDigitalInputBit(int bitnumber)
        {
            return _digitalInputBits[bitnumber];
        }

        internal BitArray DigitalInputBits
        {
            set
            {
                if (_digitalInputBits != value)
                {
                    _digitalInputBits = value;
                    log.Info($"{RobotTimestamp} ,DigitalInputBits, {_digitalInputBits}");

                }

            }
        }

        

        #endregion


        #region Digital Output Bits


        internal BitArray DigitalOutputBits
        {
            set
            {   
                if(value != _digitalOutputBits)
                {
                    _digitalOutputBits = value;
                    log.Info($"{RobotTimestamp} ,DigitalOutputBits, {_digitalOutputBits}");
                }
            }
        }

        public bool GetDigitalOutputBit(int bitNumber)
        {
            return _digitalOutputBits[bitNumber];
        }
        
        #endregion



        public int RTDEProtocolVersion
        {
            get { return _rtdeProtocolVersion; }
            set {
                if (_rtdeProtocolVersion != value)
                {
                    _rtdeProtocolVersion = value;
                    log.Info(RobotTimestamp + " ,RTDEProtocolVersion: " + _rtdeProtocolVersion);
                }
            }
        }

        public double[] ActualTCPPose
        {
            get { return _actualTCPPose; }
            set
            {
                if (!Vector6DEquals(_actualTCPPose, value, _vector6DPrecision))
                {
                    _actualTCPPose = value;
                    log.Info($"{RobotTimestamp}, ActualTCPPose,{_actualTCPPose[0]}, {_actualTCPPose[1]}, {_actualTCPPose[2]}, {_actualTCPPose[3]}, {_actualTCPPose[4]}, {_actualTCPPose[5]}");
                }
            }
        }

        public RobotMode RobotMode
        {
            get { return _robotMode; }
            set
            {
                if (_robotMode!= value)
                {
                    _robotMode = value;
                    log.Info(RobotTimestamp + " ,Robotmode, " + _robotMode);
                }
            }
        }

        public SafetyMode SafetyMode
        {
            get { return _safetyMode; }
            set {
                if (_safetyMode != value)
                {
                    _safetyMode = value;
                    log.Info(RobotTimestamp +" ,SafetyMode, " + _safetyMode);
                }
            }
        }

        public double[] TargetQ
        {
            get { return _targetQ; }
            set
            {
                if (!Vector6DEquals(_targetQ, value, _vector6DPrecision))
                {
                    _targetQ = value;
                    log.Info($"{RobotTimestamp}, TargetQ,{_targetQ[0]}, {_targetQ[1]}, {_targetQ[2]}, {_targetQ[3]}, {_targetQ[4]}, {_targetQ[5]}");
                }
            }
        }

        public double[] TargetQD
        {
            get { return _targetQD; }
            set
            {
                if (!Vector6DEquals(_targetQD, value, _vector6DPrecision))
                {
                    _targetQD = value;
                    log.Info($"{RobotTimestamp}, TargetQD,{_targetQD[0]}, {_targetQD[1]}, {_targetQD[2]}, {_targetQD[3]}, {_targetQD[4]}, {_targetQD[5]}");
                }
            }
        }

        public double[] TargetQDD
        {
            get { return _targetQDD; }
            set
            {
                if (!Vector6DEquals(_targetQDD, value, _vector6DPrecision))
                {
                    _targetQDD = value;
                    log.Info($"{RobotTimestamp}, TargetQDD,{_targetQDD[0]}, {_targetQDD[1]}, {_targetQDD[2]}, {_targetQDD[3]}, {_targetQDD[4]}, {_targetQDD[5]}");
                }
            }
        }

        public double[] TargetCurrent       //////////////////// GIVER DET MENING AT TARGET CURRENT ER VECTOR 6D ??????????????????????????
        {
            get { return _targetCurrent; }
            set
            {
                if (!Vector6DEquals(_targetCurrent, value, _vector6DPrecision))
                {
                    _targetCurrent = value;
                    log.Info($"{RobotTimestamp}, TargetCurrent,{_targetCurrent[0]}, {_targetCurrent[1]}, {_targetCurrent[2]}, {_targetCurrent[3]}, {_targetCurrent[4]}, {_targetCurrent[5]}");
                }
            }
        }

        public double[] TargetMoment        //////////////////// GIVER DET MENING AT TARGET Moment ER VECTOR 6D ??????????????????????????
        {
            get { return _targetMoment; }
            set
            {
                if (!Vector6DEquals(_targetMoment, value, _vector6DPrecision))
                {
                    _targetMoment = value;
                    log.Info($"{RobotTimestamp}, TargetMoment,{_targetMoment[0]}, {_targetMoment[1]}, {_targetMoment[2]}, {_targetMoment[3]}, {_targetMoment[4]}, {_targetMoment[5]}");
                }
            }
        }

        public double[] ActualQ
        {
            get { return _actualQ; }
            set
            {
                if (!Vector6DEquals(_actualQ, value, _vector6DPrecision))
                {
                    _actualQ = value;
                    log.Info($"{RobotTimestamp}, ActualQ,{_actualQ[0]}, {_actualQ[1]}, {_actualQ[2]}, {_actualQ[3]}, {_actualQ[4]}, {_actualQ[5]}");
                }
            }
        }

        public double[] ActualQD
        {
            get {return _actualQD;}
            set
            {
                if (!Vector6DEquals(_actualQD, value, _vector6DPrecision))
                {
                    _actualQD = value;
                    log.Info($"{RobotTimestamp}, ActualQD,{_actualQD[0]}, {_actualQD[1]}, {_actualQD[2]}, {_actualQD[3]}, {_actualQD[4]}, {_actualQD[5]}");
                }
            }
        }

        public double[] ActualCurrent
        {
            get { return _actualCurrent; }
            set
            {
                if (!Vector6DEquals(_actualCurrent, value, _vector6DPrecision))
                {
                    _actualCurrent = value;
                    log.Info($"{RobotTimestamp}, ActualCurrent,{_actualCurrent[0]}, {_actualCurrent[1]}, {_actualCurrent[2]}, {_actualCurrent[3]}, {_actualCurrent[4]}, {_actualCurrent[5]}");
                }
            }
        }

        public double[] JointControlOutput { get; set; }
        public double[] ActualTCPSpeed { get; set; }
        public double[] ActualTCPForce { get; set; }

        public double[] TargetTCPPose
        {
            get
            {
                return _targetTCPPose;
            }
            set
            {
                _targetTCPPose = value;
                //log.Info($"{RobotTimestamp}, TargetTCPPose,{_targetTCPPose.X}, {_targetTCPPose.Y}, {_targetTCPPose.Z}, {_targetTCPPose.RX}, {_targetTCPPose.RY}, {_targetTCPPose.RZ}");   //LOGSPAM
            }
        }
        public double[] TargetTCPSpeed { get; set; }
        public double[] JointTemperatures { get; set; }
        public double ActualExecutionTime { get; set; }
        public double[] JointMode { get; set; }     //must use jointmode enum
        public double[] ActualToolAccelerometer { get; set; }
        public double SpeedScaling { get; set; }
        public double TargetSpeedFraction { get; set; }
        public double ActualMomentum { get; set; }
        public double ActualMainVoltage { get; set; }
        public double ActualRobotVoltage { get; set; }
        public double ActualRobotCurrent { get; set; }
        public double[] ActualJointVoltage { get; set; }

        /// <summary>
        /// Running state of a RealTimeClient program send to the Robot
        /// </summary>
        public RuntimeState RuntimeState
        {
            get { return _runtimeState; }
            set
            {
                if (_runtimeState != value)
                {
                    _runtimeState = value;
                    log.Info($"{RobotTimestamp}, RuntimeState, {_runtimeState}");
                }
            }
        }  //probably an enum .. must fix
        public double IOCurrent { get; set; }
        public double ToolAnalogInput0 { get; set; }
        public double ToolAnalogInput1 { get; set; }
        public double ToolOutputCurrent { get; set; }
        public int ToolOutputVoltage { get; set; }
        public double StandardAnalogInput0 { get; set; }
        public double StandardAnalogInput1 { get; set; }
        public double StandardAnalogOutput0 { get; set; }
        public double StandardAnalogOutput { get; set; }

        public RobotStatus RobotStatus
        {
            get { return _robotStatus; }
            set { _robotStatus = value; }
        }

        public SafetyStatus SafetyStatus
        {
            get { return _safetyStatus; }
            set { _safetyStatus = value; }
        }

        public double TCPForceScalar { get; set; }

        public double[] ForceTourqe
        {
            get { return _forceTorque; }
            set
            {
                if (!Vector6DEquals(_forceTorque, value, _vector6DPrecision))
                {
                    _forceTorque = value;
                    log.Info($"{RobotTimestamp}, ForceTorque,{_forceTorque[0]}, {_forceTorque[1]}, {_forceTorque[2]}, {_forceTorque[3]}, {_forceTorque[4]}, {_forceTorque[5]}");
                }
            }
        }

        #region OutputBitRegisters

        public bool GetOutputBitRegister(int bitNumber)
        {
            return _outputBitRegisters[bitNumber];
        }

        internal BitArray OutputBitRegisters0to31
        {
            set
            { 
                for (int i = 0; i < 31; i++)
                {
                    if (_outputBitRegisters[i] != value[i])
                    {
                        _outputBitRegisters[i] = value[i];
                        log.Info($"{RobotTimestamp}, OutputBitRegister{i} {(bool)value[i]}");
                    }
                    i++;
                }
            }
        }

        internal BitArray OutputBitRegisters32to63
        {
            set
            {
                for (int i = 32; i < 63; i++)
                {
                    if (_outputBitRegisters[i] != value[i-32])
                    {
                        _outputBitRegisters[i] = value[i];
                        log.Info($"{RobotTimestamp}, OutputBitRegister{i} {(bool)value[i-32]}");
                    }
                    i++;
                }
            }
        }
        #endregion






        private bool Vector6DEquals(double[] firstVector6D, double[] secondVector6D, double precision)
        {
            if (firstVector6D == null || secondVector6D == null)
                return false;
            if (firstVector6D[0] - secondVector6D[0] > precision || secondVector6D[0] - firstVector6D[0] > precision )
            {
                return false;
            }
            if (firstVector6D[1] - secondVector6D[1] > precision || secondVector6D[1] - firstVector6D[1] > precision)
            {
                return false;
            }
            if (firstVector6D[2] - secondVector6D[2] > precision || secondVector6D[2] - firstVector6D[2] > precision)
            {
                return false;
            }
            if (firstVector6D[3] - secondVector6D[3] > precision || secondVector6D[3] - firstVector6D[3] > precision)
            {
                return false;
            }
            if (firstVector6D[4] - secondVector6D[4] > precision || secondVector6D[4] - firstVector6D[4] > precision)
            {
                return false;
            }
            if (firstVector6D[5] - secondVector6D[5] > precision || secondVector6D[5] - firstVector6D[5] > precision)
            {
                return false;
            }
            return true;
        }
    }
}
