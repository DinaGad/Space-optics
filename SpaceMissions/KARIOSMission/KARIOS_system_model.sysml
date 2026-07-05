/**
 * =====================================================================
 *  KARIOS CubeSat -- SysML v2 System Model
 *  KAIST Intelligence & Reconnaissance Orbital Satellite
 *
 *  Instantiated from the INCOSE SSWG CubeSat Reference Model (CRM);
 *  method adapted from the RANDEV CubeSat MBSE description.
 *
 *  Language : SysML v2 (KerML) textual notation.
 *  Target   : SysML v2 pilot implementation / SysIDE / Cameo (v2).
 *  Note     : minor tool-specific syntax tweaks may be required on import.
 * =====================================================================
 */
package 'KARIOS System Model' {

    private import ScalarValues::*;

    // =================================================================
    //  0.  VALUE TYPES  (engineering quantities, SI units in doc)
    // =================================================================
    package ValueTypes {
        attribute def Mass       :> Real; // kg
        attribute def Power      :> Real; // W
        attribute def Energy     :> Real; // Wh
        attribute def DataRate   :> Real; // kbps
        attribute def DataVolume :> Real; // MB
        attribute def Angle      :> Real; // deg
        attribute def Duration   :> Real; // s
        attribute def Frequency  :> Real; // MHz
        attribute def Ratio      :> Real; // dimensionless
        attribute def Altitude   :> Real; // km
    }
    private import ValueTypes::*;

    // =================================================================
    //  1.  MISSION CONTEXT  (CubeSat Domain -- external entities)
    // =================================================================
    package MissionContext {
        part def SpaceEnvironment;          // radiation, thermal, vacuum, debris
        part def EarthEnvironment;          // atmosphere, gravity field
        part def LaunchProvider;            // transport / launch / deploy services
        part def RegulatoryAuthority;       // spectrum & orbital-debris licensing
        part def SIGINTTarget;              // RF emitters of interest (mission target)

        part def GroundStation {
            port uhfLink   : ~RFPort;       // UHF TT&C
            port loraLink  : ~RFPort;       // LoRaWAN payload/telemetry
        }

        // Human / organisational actors
        part def MissionOperator;
        part def CyberResearcher;           // IITP AI-vulnerability experiments
    }

    // =================================================================
    //  2.  PORTS & INTERFACES  (for the Internal Block view)
    // =================================================================
    package Interfaces {
        item def PowerFlow    { attribute voltage : Real; }   // V
        item def DataFrame    { attribute size : DataVolume; }
        item def RFSignal     { attribute freq : Frequency; }
        item def AttitudeCmd;

        port def PowerPort   { out item pwr : PowerFlow; }
        port def DataPort    {  inout item data : DataFrame; }
        port def RFPort      { out item rf : RFSignal; }
        port def CmdPort     { in  item cmd : AttitudeCmd; }
    }
    private import Interfaces::*;

    // =================================================================
    //  3.  STRUCTURE  (BDD / IBD -- system decomposition)
    // =================================================================
    package Structure {

        // ---- Enterprise / mission level ----
        part def KARIOS_Mission {
            part spaceSegment  : KARIOS_Spacecraft;
            part groundSegment : GroundSegment;
            part launchSegment : MissionContext::LaunchProvider;
        }

        part def GroundSegment {
            part primaryGS : MissionContext::GroundStation;
            part backupGS  : MissionContext::GroundStation[0..*];
        }

        // ---- Space segment ----
        part def KARIOS_Spacecraft {
            attribute totalMass : Mass;           // <= platform allocation
            attribute formFactor : String = "6U"; // CubeSat units

            part bus           : Bus;
            part sigintPayload : SIGINTPayload;   // primary payload
            part cyberPayload  : CyberSecPayload; // secondary payload

            // externally visible ports
            port uhf  : RFPort;
            port lora : RFPort;

            // orbit as an attribute set (see Analysis::Orbit)
            attribute redefines totalMass;
        }

        // ---- Bus (platform) ----
        part def Bus {
            part obc      : OBC;
            part eps      : EPS;
            part adcs     : ADCS;
            part comm     : CommsSubsystem;
            part structure: StructureSubsystem;
            part thermal  : ThermalSubsystem;

            // internal wiring (IBD): power distribution & data bus
            connect eps.powerOut  to obc.powerIn;
            connect eps.powerOut  to adcs.powerIn;
            connect eps.powerOut  to comm.powerIn;
            connect obc.dataBus   to comm.dataIn;
            connect obc.cmdOut    to adcs.cmdIn;
        }

        part def OBC {
            port powerIn : ~PowerPort;
            port dataBus : DataPort;
            port cmdOut  : CmdPort;
            attribute storage : DataVolume; // on-board buffer
        }
        part def EPS {
            port powerOut : PowerPort[1..*];
            attribute batteryCapacity : Energy;
            attribute arrayPower      : Power; // BOL generation
        }
        part def ADCS {
            port powerIn : ~PowerPort;
            port cmdIn   : ~CmdPort;
            attribute pointingAccuracy : Angle;
        }
        part def CommsSubsystem {
            port powerIn : ~PowerPort;
            port dataIn  : ~DataPort;
            port uhfOut  : RFPort;   // TT&C
            port loraOut : RFPort;   // payload downlink
            attribute uhfRate  : DataRate;
            attribute loraRate : DataRate;
        }
        part def StructureSubsystem { attribute mass : Mass; }
        part def ThermalSubsystem   { attribute controlRange : String = "-20..+50 C"; }

        // ---- Payloads ----
        part def SIGINTPayload {
            port powerIn : ~PowerPort;
            port dataOut : DataPort;
            attribute freqBand   : String;
            attribute swath      : Angle;
            attribute dutyCycle  : Ratio;
        }
        part def CyberSecPayload {
            port powerIn : ~PowerPort;
            port dataOut : DataPort;
            doc /* AI-enhanced satellite-vulnerability discovery target
                   (vulnerable OBC, LoRaWAN, EPS attack surfaces). */
        }
    }
    private import Structure::*;

    // =================================================================
    //  4.  BEHAVIOR  (use cases, activities, state machine)
    // =================================================================
    package Behavior {

        // ---- Use cases ----
        use case def CollectSIGINT {
            subject karios : KARIOS_Spacecraft;
            actor target   : MissionContext::SIGINTTarget;
        }
        use case def DistributeMissionData {
            subject karios : KARIOS_Spacecraft;
            actor operator : MissionContext::MissionOperator;
        }
        use case def OperateSpacecraft {
            subject karios : KARIOS_Spacecraft;
            actor operator : MissionContext::MissionOperator;
        }
        use case def RunCyberExperiment {
            subject karios : KARIOS_Spacecraft;
            actor researcher : MissionContext::CyberResearcher;
        }

        // ---- Activity : Collect & Distribute Mission Data ----
        action def CollectAndDistributeMissionData {
            in  tasking  : Interfaces::AttitudeCmd;
            out delivered: Interfaces::DataFrame;

            action generateTasking;
            action collectData      { out raw : Interfaces::DataFrame; }
            action storeOnBoard     { in  raw : Interfaces::DataFrame; }
            action downlinkData     { out delivered : Interfaces::DataFrame; }

            // control/data flow
            first generateTasking then collectData;
            flow collectData.raw to storeOnBoard.raw;
            then downlinkData;
        }

        // ---- State machine (operational states; may overlap) ----
        state def KARIOS_Operations {
            entry action initialize;

            state orbitState {
                state Launched;
                state Operational;
                transition Launched then Operational;
            }
            state solarState {
                state Sunlight;
                state Eclipse;
                transition Sunlight then Eclipse;
                transition Eclipse  then Sunlight;
            }
            state payloadState {
                state Idle;
                state Collecting;
                transition Idle then Collecting;
                transition Collecting then Idle;
            }
            state downloadState {
                state NotTransmitting;
                state Transmitting;   // only within ground-station access
                transition NotTransmitting then Transmitting;
                transition Transmitting then NotTransmitting;
            }
        }
    }

    // =================================================================
    //  5.  ANALYSIS  (parametric constraint blocks -- budgets)
    // =================================================================
    package Analysis {

        // Orbit (SSO ~550 km) -- values from the STK pre-launch analysis
        attribute def Orbit {
            attribute altitude    : Altitude  = 550;      // km
            attribute inclination : Angle     = 97.7444;  // deg
            attribute period      : Duration  = 5805;      // s (96.75 min)
            attribute eclipseFrac : Ratio;
        }

        // Power budget : generation vs. load and battery state
        constraint def PowerBudget {
            in arrayPower     : Power;
            in avgLoad        : Power;
            in eclipseFrac    : Ratio;
            in batteryCapacity: Energy;
            // orbit-average energy balance must be non-negative
            arrayPower * (1 - eclipseFrac) >= avgLoad
        }

        // Data budget : collected volume must be downlinked per day
        constraint def DataBudget {
            in collectRate   : DataRate;
            in collectTime   : Duration;
            in downlinkRate  : DataRate;
            in contactTime   : Duration;   // from STK access analysis
            downlinkRate * contactTime >= collectRate * collectTime
        }

        // Link budget : received Eb/N0 must exceed threshold
        constraint def LinkBudget {
            in eirp        : Real;   // dBW
            in pathLoss    : Real;   // dB
            in gainOverT   : Real;   // dB/K
            in required    : Real;   // dB  (Eb/N0 threshold + margin)
            (eirp - pathLoss + gainOverT) >= required
        }

        // Coverage / revisit (evaluated in STK, fed back here)
        constraint def CoverageBudget {
            in revisitTime   : Duration;
            in requiredRevisit : Duration;
            revisitTime <= requiredRevisit
        }
    }

    // =================================================================
    //  6.  REQUIREMENTS  (with satisfy / verify traceability -> RVM)
    // =================================================================
    package Requirements {

        requirement def <'MR'> MissionRequirement { subject karios : KARIOS_Spacecraft; }

        requirement <'MR-1'> collectSIGINT : MissionRequirement {
            doc /* KARIOS shall collect SIGINT data over the target region
                   at the specified revisit and swath. */
        }
        requirement <'MR-2'> secondaryCyber : MissionRequirement {
            doc /* KARIOS shall host a cybersecurity payload for AI-based
                   on-orbit vulnerability experiments. */
        }
        requirement <'SR-1'> powerPositive : MissionRequirement {
            doc /* The orbit-average power balance shall be non-negative
                   including eclipse. */
            require constraint : Analysis::PowerBudget;
        }
        requirement <'SR-2'> dataDownlinked : MissionRequirement {
            doc /* All collected mission data shall be downlinked within
                   the available daily ground-station contact time. */
            require constraint : Analysis::DataBudget;
        }
        requirement <'SR-3'> linkMargin : MissionRequirement {
            doc /* The communications link shall close with positive margin. */
            require constraint : Analysis::LinkBudget;
        }
        requirement <'SR-4'> revisitTime : MissionRequirement {
            doc /* Target-region revisit time shall meet the mission need. */
            require constraint : Analysis::CoverageBudget;
        }
        requirement <'SR-5'> disposalCompliance : MissionRequirement {
            doc /* The spacecraft shall re-enter within the applicable
                   orbital-debris disposal guideline. */
        }

        // ---- Satisfy : which parts satisfy which requirements ----
        satisfy collectSIGINT      by Structure::KARIOS_Spacecraft::sigintPayload;
        satisfy secondaryCyber     by Structure::KARIOS_Spacecraft::cyberPayload;
        satisfy powerPositive      by Structure::Bus::eps;
        satisfy dataDownlinked     by Structure::Bus::comm;
        satisfy linkMargin         by Structure::Bus::comm;

        // ---- Verify : method allocation (I/A/D/T -> Verification Process) ----
        // MR-1 : Analysis (STK coverage) + Demonstration (payload)
        // SR-1 : Analysis (power budget parametric) + Test (TVAC/EPS)
        // SR-2 : Analysis (data budget) + Demonstration (DITL)
        // SR-3 : Analysis (link budget) + Test (RF)
        // SR-4 : Analysis (STK revisit)
        // SR-5 : Analysis (STK lifetime / re-entry)
    }
}
