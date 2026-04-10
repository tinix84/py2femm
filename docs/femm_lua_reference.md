# FEMM 4.2 Lua Scripting Reference

> Extracted from the FEMM 4.2 User Manual (October 25, 2015)

Chapter3
Lua Scripting
3.1 WhatLuaScripting?
The Lua extension language has been used to add scripting/ba tch processing facilities to FEMM.
The Interactive Shell can run Lua scripts through the Open Lua Script selection on the Files
menu,orLuacommandscan beentered indirectlyto theLuaCon soleWindow.
Lua is a complete, open-source scripting language. Source c ode for Lua, in addition to de-
tailed documentation about programming in Lua, can be obtai ned from the Lua homepage at
http://www.lua.org . Because thescriptingﬁles aretext,theycan beeditedwith anytexteditor
(e.g.notepad). As of this writing, the latest release of Lua is ver sion 5.0. However, the version of
LuaincorporatedintoFEMMis Lua4.0.
In addition to the standard Lua command set described in [9], a number of FEMM-speciﬁc
functions have been added for manipulating ﬁles in both the p re- and post-processor. These com-
mandsare describedin thefollowingsections.
3.2 CommonLua CommandSet
AnumberofFEMM-speciﬁcLuacommandsexistthatarenotasso ciatedwithanyparticularprob-
lemtype.
•clearconsole() Clears theoutputwindowoftheLuaconsole.
•newdocument(doctype) Createsanewpreprocessordocumentandopensupanewprepro -
cessor window. Specify doctype to be0for a magnetics problem, 1for an electrostatics
problem, 2for a heat ﬂow problem, or 3for a current ﬂow problem. An alternative syntax
forthiscommandis create(doctype)
•hideconsole() Hides theﬂoating Luaconsolewindow.
•hidepointprops() HidestheﬂoatingFEMMProperties displaywindow.
•messagebox("message") displaysthe "message" stringtothescreeninapop-upmessage
box.
82

---

•open("filename") Opensadocumentspeciﬁed by filename .
•pause() Waits fortheokbuttontobepressed, adebughelper.
•print() This is standard Lua “print” command directed to the output o f the Lua console
window. Any number of comma-separated items can be printed a t once via the print com-
mand.
•prompt("message") This function allows a Lua script to prompt a user for input. W hen
thiscommandisused,adialogboxpopsupwiththe "message" stringonthetitlebarofthe
dialogbox. Theusercanenterinasinglelineofinputviathe dialogbox. promptreturnsthe
user’sinputasastring. Ifanumericalvalueisdesired,the syntax tonumber(prompt("message"))
can beused.
•quit()Close all documents and exit the the Interactive Shell at the end of the currently
executingLuascript.
•setcompatibilitymode(value) Ifvalueissetto 1,variousmagnetics-relatedcommands
with complex arguments revert to their deﬁnitions in the FEM M 4.1 manual. If valueis
set to0, the FEMM 4.2 deﬁnitions are used. The default mode is compat ibility mode 0.
Affected functionsinclude:
–miaddmaterial
–mimodifymaterial
–miaddpointprop
–mimodifypointprop
–miaddcircprop
–mimodifycircprop
–mogetpointvalues
–molineintegral
–moblockintegral
–mogetcircuitproperties
•showconsole() DisplaystheﬂoatingLuaconsolewindow.
•showpointprops() DisplaystheﬂoatingFEMM Properties displaywindow.
•smartmesh(state) Calling with a state of 0 turns off “smart mesh” functionalit y for the
present session; calling with a state of 1 turns “smarth mesh ing” on. The setting os not
permanent–usingthePreferences settingtopermanentlytu rn onoroff.
3.3 MagneticsPreprocessorLuaCommandSet
A number of different commands are available in the preproce ssor. Two naming conventions can
beused: onewhichseparateswordsinthecommandnamesbyund erscores,andonethateliminates
theunderscores.
83

---

3.3.1 Object Add/Remove Commands
•miaddnode(x,y) Adda newnodeatx,y
•miaddsegment(x1,y1,x2,y2) Add a new line segment from node closest to (x1,y1) to
nodeclosest to(x2,y2)
•miaddblocklabel(x,y) Addanew blocklabel at (x,y)
•miaddarc(x1,y1,x2,y2,angle,maxseg) Add a new arc segment from the nearest node
to(x1,y1)tothenearest nodeto (x2,y2)withangle‘angle’d ividedinto‘maxseg’segments.
•mideleteselected Deleteallselected objects.
•mideleteselectednodes Deleteselectednodes.
•mideleteselectedlabels Deleteselected blocklabels.
•mideleteselectedsegments Deleteselected segments.
•mideleteselectedarcsegments Deleteselects arcs.
3.3.2 GeometrySelection Commands
•miclearselected() Clear all selectednodes, blocks,segmentsand arcsegments .
•miselectsegment(x,y) Select thelinesegmentclosestto(x,y)
•miselectnode(x,y) Select the node closest to (x,y). Returns the coordinates of the se-
lected node.
•miselectlabel(x,y) Select the label closet to (x,y). Returns the coordinates of the se-
lected label.
•miselectarcsegment(x,y) Select thearc segmentclosestto (x,y)
•miselectgroup(n) Selectthe nthgroupofnodes,segments,arcsegmentsandblocklabels.
Thisfunctionwillclearallpreviouslyselectedelementsa ndleavetheeditmodein4(group)
•miselectcircle(x,y,R,editmode) selectsobjectswithinacircleofradiusRcenteredat
(x,y). If only x, y, and R paramters are given,thecurrent edi t mode is used. If theeditmode
parameter is used, 0 denotes nodes, 2 denotes block labels, 2 denotes segments, 3 denotes
arcs, and 4 speciﬁes thatallentitytypes aretobeselected.
•miselectrectangle(x1,y1,x2,y2,editmode) selectsobjectswithinarectangledeﬁned
bypoints(x1,y1)and(x2,y2). Ifnoeditmodeparameterissu pplied,thecurrenteditmodeis
used. If the editmode parameter is used, 0 denotes nodes, 2 de notes block labels, 2 denotes
segments,3 denotesarcs, and 4 speciﬁes thatall entitytype s areto beselected.
84

---

3.3.3 Object Labeling Commands
•misetnodeprop("propname",groupno) Settheselectednodestohavethenodalproperty
mi"propname" and groupnumber groupno.
•misetblockprop("blockname", automesh, meshsize, "incircu it", magdirection,
group, turns) Set theselected blocklabels tohavetheproperties:
–Block property "blockname" .
–automesh : 0=mesherdeferstomeshsizeconstraintdeﬁnedin meshsize ,1=mesher
automaticallychoosesthemeshdensity.
–meshsize : sizeconstrainton themesh intheblockmarked bythislabel .
–Block is amemberofthecircuitnamed "incircuit"
–The magnetization is directed along an angle in measured in d egrees denoted by the
parameter magdirection . Alternatively, magdirection can be a string containing a
formula that prescribes the magnetization direction as a fu nction of element position.
Inthisformula thetaandRdenotestheangleindegreesofalineconnectingthecenter
each element with the origin and the length of this line, resp ectively; xandydenote
the x- and y-position of the center of the each element. For ax isymmetricproblems, r
andzshouldbeusedinplace of xandy.
–A memberofgroupnumber group
–Thenumberofturns associatedwiththislabelis denotedby turns.
•misetsegmentprop("propname", elementsize, automesh, hide , group) Setthese-
lect segmentstohave:
–Boundary property "propname"
–Local element sizealong segmentno greaterthan elementsize
–automesh : 0 = mesher defers to the element constraint deﬁned by elementsize , 1 =
mesherautomaticallychooses meshsizealongtheselecteds egments
–hide: 0 =nothiddenin post-processor,1== hiddeninpostprocess or
–A memberofgroupnumber group
•misetarcsegmentprop(maxsegdeg, "propname", hide, group) Set the selected arc
segmentsto:
–Meshed withelementsthatspan at most maxsegdeg degrees perelement
–Boundary property "propname"
–hide: 0 =nothiddenin post-processor,1== hiddeninpostprocess or
–A memberofgroupnumber group
•misetgroup(n) Set thegroupassociated oftheselected itemston
85

---

3.3.4 Problem Commands
•miprobdef(frequency,units,type,precision,(depth),(min angle),(acsolver) changes
theproblemdeﬁnition. Set frequency tothedesiredfrequencyinHertz. The unitsparam-
eterspeciﬁestheunitsusedformeasuringlengthintheprob lemdomain. Valid "units" en-
triesare "inches" ,"millimeters" ,"centimeters" ,"mils","meters,and"micrometers" .
Set the parameter problemtype to"planar" for a 2-D planar problem, or to "axi"for an
axisymmetric problem. The precision parameter dictates the precision required by the
solver. For example, entering 1E-8requires the RMS of the residual to be less than 10−8.
A ﬁfth parameter, representing the depth of the problem in th e into-the-page direction for
2-D planar problems, can also also be speciﬁed. A sixthparam eter represents theminimum
angleconstraintsent tothemeshgenerator. A seventhparam eterspeciﬁes thesolvertypeto
beusedforAC problems.
•mianalyze(flag) runsfkerntosolvetheproblem. The flagparametercontrolswhether
thefkernwindowisvisibleorminimized. Foravisiblewindow,either specifynovaluefor
flagorspecify 0. Foraminimizedwindow, flagshouldbesetto 1.
•miloadsolution() loadsanddisplaysthesolutioncorrespondingtothecurren tgeometry.
•misetfocus("documentname") Switches the magnetics input ﬁle upon which Lua com-
mands are to act. If more than one magnetics input ﬁle is being edited at a time, this com-
mand can be used to switch between ﬁles so that the mutiple ﬁle s can be operated upon
programmaticallyviaLua. documentname shouldcontainthenameofthedesireddocument
as itappears on thewindow’stitlebar.
•misaveas("filename") savestheﬁlewithname "filename" . Noteifyouuseapathyou
mustusetwo backslashes e.g."c:\\temp\\myfemmfile.fem"
3.3.5 MeshCommands
•micreatemesh() runstriangletocreateamesh. Notethatthisisnotanecessa ry precursor
of performing an analysis, as mianalyze() will make sure the mesh is up to date before
runningan analysis. Thenumberofelements inthemeshispus hedback ontotheluastack.
•mishowmesh() showsthemesh.
•mipurgemesh() clears themeshoutofboththescreen and memory.
3.3.6 Editing Commands
•micopyrotate(bx, by, angle, copies, (editaction) )
–bx, by– basepointforrotation
–angle– angle by which the selected objects are incrementally shif ted to make each
copy.angleis measuredin degrees.
–copies– numberofcopies tobeproduced fromtheselected objects.
86

---

•micopytranslate(dx, dy, copies, (editaction))
–dx,dy– distancebywhichtheselected objectsare incrementallys hifted.
–copies– numberofcopies tobeproduced fromtheselected objects.
–editaction 0–nodes,1–lines(segments),2–blocklabels,3–arcsegmen ts,4-group
•micreateradius(x,y,r) turnsacornerlocatedat (x,y)intoacurveofradius r.
•mimoverotate(bx,by,shiftangle (editaction))
–bx, by– basepointforrotation
–shiftangle – angleindegrees by whichtheselectedobjectsare rotated.
–editaction 0–nodes,1–lines(segments),2–blocklabels,3–arcsegmen ts,4-group
•mimovetranslate(dx,dy,(editaction))
–dx,dy– distancebywhichtheselected objectsare shifted.
–editaction 0–nodes,1–lines(segments),2–blocklabels,3–arcsegmen ts,4-group
•miscale(bx,by,scalefactor,(editaction))
–bx, by– basepointforscaling
–scalefactor – amultiplierthatdetermineshowmuch theselected objects are scaled
–editaction 0–nodes,1–lines(segments),2–blocklabels,3–arcsegmen ts,4-group
•mimirror(x1,y1,x2,y2,(editaction)) mirrortheselected objectsabout alinepassing
through the points (x1,y1) and(x2,y2). Valid editaction entries are 0 for nodes, 1 for
lines(segments),2 forblock labels,3for arcsegments,and 4 forgroups.
•miseteditmode(editmode) Sets thecurrent editmodeto:
–"nodes" -nodes
–"segments" - linesegments
–"arcsegments" -arc segments
–"blocks" -blocklabels
–"group" -selected group
Thiscommandwillaffectallsubsequentusesoftheotheredi tingcommands,iftheyareused
WITHOUT the editaction parameter.
87

---

3.3.7 ZoomCommands
•mizoomnatural() zoomstoa“natural”viewwith sensibleextents.
•mizoomout() zoomsoutbyafactor of50%.
•mizoomin() zoominby afactorof200%.
•mizoom(x1,y1,x2,y2) Set the display area to be from the bottom left corner speciﬁe d by
(x1,y1)tothetoprightcorner speciﬁed by (x2,y2).
3.3.8 ViewCommands
•mi_showgrid() Show thegrid points.
•mi_hidegrid() Hidethegridpointspoints.
•mi_grid_snap("flag") Setting flagto ”on” turns on snap to grid, setting flagto"off"
turnsoffsnapto grid.
•mi_setgrid(density,"type") Change the grid spacing. The density parameter speci-
ﬁes the space between grid points, and the typeparameter is set to "cart"for cartesian
coordinatesor "polar" forpolarcoordinates.
•mirefreshview() Redraws thecurrent view.
•miminimize() minimizestheactivemagneticsinputview.
•mimaximize() maximizestheactivemagneticsinputview.
•mirestore() restores the active magnetics input view from a minimized or maximized
state.
•miresize(width,height) resizes theactivemagnetics inputwindowclient area to wid th
×height.
3.3.9 Object Properties
•migetmaterial("materialname") fetchesthematerialspeciﬁedby materialname from
thematerialslibrary.
•miaddmaterial("materialname", mu x, mu y, Hc, J, Cduct, Lam d, Phi hmax,
lamfill, LamType, Phi hx, Phi hy,NStrands,WireD )addsanewmaterialwithcalled
"materialname" withthematerialproperties:
–muxRelativepermeabilityin thex-orr-direction.
–muyRelativepermeabilityin they-orz-direction.
–HcPermanent magnetcoercivityinAmps/Meter.
88

---

–JReal Appliedsourcecurrent densityin Amps/mm2.
–CductElectrical conductivityofthematerial inMS/m.
–LamdLaminationthicknessin millimeters.
–PhihmaxHysteresislag anglein degrees,used fornonlinearBH curve s.
–LamfillFraction of the volume occupied per lamination that is actua lly ﬁlled with
iron(Notethatthisparameterdefaultsto1the femmepreprocessordialogboxbecause,
by default,iron completelyﬁllsthevolume)
–Lamtype Set to
∗0 –Not laminatedorlaminatedin plane
∗1 –laminatedx orr
∗2 –laminatedy orz
∗3 –Magnet wire
∗4 –Plain stranded wire
∗5 –Litzwire
∗6 –Square wire
–PhihxHysteresislag indegrees inthex-directionforlinearprob lems.
–PhihyHysteresislag indegrees inthey-directionforlinearprob lems.
–NStrands Numberofstrandsinthewirebuild. Shouldbe1forMagnetorS quarewire.
–WireDDiameterofeach wireconstituentstrand inmillimeters.
Notethatnotallpropertiesneedbedeﬁned–propertiesthat aren’tdeﬁnedareassigneddefault
values.
•miaddbhpoint("blockname",b,h) Adds a B-H data point the the material speciﬁed by
thestring "blockname" . Thepointtobeadded has aﬂux densityof binunitsofTeslasand
aﬁeld intensityof hinunitsofAmps/Meter.
•miclearbhpoints("blockname") ClearsallB-Hdatapointsassociatiedwiththematerial
speciﬁed by "blockname" .
•miaddpointprop("pointpropname",a,j) addsanewpointpropertyofname "pointpropname"
witheitheraspeciﬁedpotential ainunitsWebers/Meterorapointcurrent jinunitsofAmps.
Set theunusedparameterpairs to0.
•miaddboundprop("propname", A0, A1, A2, Phi, Mu, Sig, c0, c1, B dryFormat)
addsa newboundaryproperty withname "propname"
–Fora“PrescribedA”typeboundarycondition,setthe A0, A1, A2 andPhiparameters
as required. Set all otherparametersto zero.
–For a “Small Skin Depth” type boundary condtion, set the Muto the desired relative
permeability and Sigto the desired conductivity in MS/m. Set BdryFormat to 1 and
all otherparameters tozero.
89

---

–Toobtaina“Mixed”typeboundarycondition,set C1andC0asrequiredand BdryFormat
to 2. Set allotherparameters tozero.
–Fora“Strategicdualimage”boundary,set BdryFormat to3andsetallotherparameters
to zero.
–Fora“Periodic”boundarycondition,set BdryFormat to4 andsetall otherparameters
to zero.
–Foran“Anti-Perodic”boundarycondition,set BdryFormat to5setallotherparameters
to zero.
•miaddcircprop("circuitname", i, circuittype)
adds a new circuit property with name "circuitname" with a prescribed current, i. The
circuittype parameter is 0 for a parallel-connected circuit and 1 for a se ries-connected
circuit.
•mideletematerial("materialname") deletesthematerialnamed "materialname" .
•mideleteboundprop("propname") deletes theboundary propertynamed "propname" .
•mideletecircuit("circuitname") deletesthecircuit named circuitname .
•mideletepointprop("pointpropname") deletesthepointpropertynamed "pointpropname"
•mi_modifymaterial("BlockName",propnum,value) This function allows for modiﬁca-
tion ofa material’s properties withoutredeﬁning the entir ematerial ( e.g.so that current can
be modiﬁed from run to run). The material to be modiﬁed is spec iﬁed by "BlockName" .
The next parameter is the number of the property to be set. The last number is the value to
be applied to the speciﬁed property. The various properties that can be modiﬁed are listed
below:
propnum Symbol Description
0 BlockName Nameofthematerial
1 µx x (orr)direction relativepermeability
2 µy y (orz) directionrelativepermeability
3 Hc Coercivity,Amps/Meter
4 Jr Source current density,MA/m2
5 σ Electrical conductivity,MS/m
6 dlam Laminationthickness,mm
7 φhmax Hysteresislag anglefornonlinearproblems,degrees
8 LamFill Iron ﬁll fraction
9 LamType 0 =None/In plane,1 =parallel tox, 2=parallelto y
10 φhx Hysteresislag inx-directionfor linearproblems,degrees
11 φhy Hysteresislag iny-directionfor linearproblems,degrees
•mi_modifyboundprop("BdryName",propnum,value) This function allows for modiﬁca-
tion of a boundary property. The BC to be modiﬁed is speciﬁed b y"BdryName" . The next
parameteristhenumberofthepropertyto beset. Thelastnum beristhevaluetobeapplied
tothespeciﬁed property. Thevariousproperties thatcan be modiﬁedare listedbelow:
90

---

propnum Symbol Description
0 BdryName Nameofboundaryproperty
1 A0 Prescribed A parameter
2 A1 Prescribed A parameter
3 A2 Prescribed A parameter
4 φ Prescribed A phase
5 µ Small skindepthrelativepermeability
6 σ Small skindepthconductivity,MS/m
7 c0 MixedBC parameter
8 c1 MixedBC parameter
9 BdryFormat Typeofboundarycondition:
0 =Prescribed A
1 =Small skindepth
2 =Mixed
3 =StrategicDualImage
4 =Periodic
5 =Antiperiodic
•mi_modifypointprop("PointName",propnum,value) This function allows for modiﬁ-
cation of a point property. The point property to be modiﬁed i s speciﬁed by "PointName" .
The next parameter is the number of the property to be set. The last number is the value to
be applied to the speciﬁed property. The various properties that can be modiﬁed are listed
below:
propnum Symbol Description
0 PointName Nameofthepointproperty
1 A Nodalpotential,Weber/Meter
2 J Nodalcurrent, Amps
•mi_modifycircprop("CircName",propnum,value) This function allows for modiﬁca-
tion of a circuit property. The circuit property to be modiﬁe d is speciﬁed by "CircName" .
The next parameter is the number of the property to be set. The last number is the value to
be applied to the speciﬁed property. The various properties that can be modiﬁed are listed
below:
propnum Symbol Description
0 CircName Nameofthecircuitproperty
1 i Total current
2 CircType 0 =Parallel, 1 =Series
3.3.10 Miscellaneous
•misavebitmap("filename") saves a bitmapped screenshot of the current view to the ﬁle
speciﬁed by "filename" , subject to the printf-type formatting explained previously for
thesavefemmfile command.
91

---

•misavemetafile("filename") saves a metaﬁle screenshot of the current view to the ﬁle
speciﬁed by "filename" , subject to the printf-type formatting explained previously for
thesavefemmfile command.
•mirefreshview() Redraws thecurrent view.
•miclose() Closes current magnetics preprocessor document and destro ys magnetics pre-
processorwindow.
•mishownames(flag) Thisfunction allowtheuserto displayor hidetheblocklabe l names
on screen. To hide the block label names, flagshould be 0. To display the names, the
parametershouldbesetto 1.
•mireaddxf("filename") Thisfunctionimportsadxfﬁlespeciﬁed by "filename" .
•misavedxf("filename") This function saves geometry informationin a dxf ﬁle speciﬁ ed
by"filename" .
•midefineouterspace(Zo,Ro,Ri) deﬁnes an axisymmetric external region to be used in
conjuction with the Kelvin Transformation method of modeli ng unbounded problems. The
Zoparameteristhez-locationoftheoriginoftheouterregion ,theRoparameteristheradius
of the outer region, and the Riparameter is the radius of the inner region ( i.e.the region
of interest). In the exterior region, the permeability vari es as a function of distance from
the origin of the external region. These parameters are nece ssary to deﬁne the permeability
variationin theexternalregion.
•miattachouterspace() marksallselectedblocklabelsasmembersoftheexternalre gion
usedformodelingunboundedaxisymmetricproblemsviatheK elvinTransformation.
•midetachouterspace() undeﬁnes all selected block labels as members of the externa l
regionusedformodelingunboundedaxisymmetricproblemsv iatheKelvinTransformation.
•miattachdefault() marks the selected block label as the default block label. Th is block
labelis appliedtoany regionthathas notbeen explicitlyla beled.
•midetachdefault() undeﬁnes thedefaultattributefortheselected blocklabel s.
•mimakeABC(n,R,x,y,bc) creates a series of circular shells that emulate the impedan ce of
an unboundeddomain (i.e. an InprovisedAsymptoticBoundar y Condition). The nparame-
ter containsthe numberofshells to be used (shouldbe betwee n 1 and 10), Ris theradius of
thesolutiondomain,and (x,y)denotesthecenterofthesolutiondomain. The bcparameter
should be speciﬁed as 0 for a Dirichlet outer edge or 1 for a Neu mann outer edge. If the
functionis called withoutall theparameters, thefunction makesup reasonablevaluesforthe-
missingparameters.
•misetprevious(filename) deﬁnes the previous solution to be used as the basis for an
ACincrementalpermeabilitysolution. Theﬁlenameshouldi ncludethe .ansextension, e.g.
misetprevious("mymodel.ans")
92

---

3.4 MagneticsPostProcessorCommandSet
There are a numberof Lua scripting commands designed to oper ate in the postprocessor. As with
the preprocessor commands, these commands can be used with e ither the underscore naming or
withtheno-underscorenamingconvention.
3.4.1 DataExtractionCommands
•molineintegral(type) Calculatethelineintegralforthedeﬁned contour
typename values 1 values 2 values 3 values 4
0 B.n total B.n avg B.n - -
1 H.t total H.t avg H.t - -
2 Contour length surface area - -
3 Stress Tensor Force DCr/x force DCy/z force 2 ×r/x force 2 ×y/z force
4 Stress Tensor Torque DCtorque 2 ×torque - -
5 (B.n)ˆ2 total (B.n)ˆ2 avg (B.n)ˆ2 - -
Returns typicallytwo (possiblycomplex)valuesas results . For force and torqueresults, the
2×results are only relevant for problems where ω/\egatio\slash=0. The 1×results are only relevant
for incremental permeability AC problems. The 1 ×results represent the force and torque
interactionsbetweenthesteady-stateand theincremental ACsolution.
•moblockintegral(type) Calculateablockintegralfortheselected blocks
93

---

Type Deﬁnition
0A·J
1 A
2 Magneticﬁeld energy
3 Hysteresisand/orlaminationlosses
4 Resistivelosses
5 Block cross-sectionarea
6 Totallosses
7 Totalcurrent
8 Integralof Bx(orBr)overblock
9 Integralof By(orBz)overblock
10 Block volume
11 x (orr)part ofsteady-stateLorentzforce
12 y (orz)part ofsteady-stateLorentzforce
13 x (orr)part of2 ×Lorentzforce
14 y (orz)part of2 ×Lorentzforce
15 Steady-stateLorentztorque
16 2×componentofLorentztorque
17 Magneticﬁeld coenergy
18 x (orr)part ofsteady-stateweightedstresstensorforce
19 y (orz)part ofsteady-stateweightedstresstensorforce
20 x (orr)part of2 ×weightedstresstensorforce
21 y (orz)part of2 ×weightedstresstensorforce
22 Steady-stateweightedstresstensortorque
23 2×componentofweightedstresstensortorque
24R2(i.e.momentofinertia/ density)
25 x (orr)part of1 ×weightedstresstensorforce
26 y (orz)part of1 ×weightedstresstensorforce
27 1×componentofweightedstresstensortorque
28 x (orr)part of1 ×Lorentzforce
29 y (orz)part of1 ×Lorentzforce
30 1×componentofLorentztorque
Thisfunctionreturnsone(possiblycomplex)value, e.g.:volume = mo blockintegral(10)
•mogetpointvalues(X,Y) Get thevalues associatedwiththepointat x,yRETURN values
inorder
94

---

Symbol Deﬁnition
A vectorpotentialA orﬂux φ
B1 ﬂux density Bxifplanar, Brifaxisymmetric
B2 ﬂux density Byifplanar, Bzifaxisymmetric
Sig electrical conductivity σ
E stored energy density
H1 ﬁeld intensity Hxifplanar, Hrifaxisymmetric
H2 ﬁeld intensity Hyifplanar, Hzifaxisymmetric
Je eddy current density
Js sourcecurrent density
Mu1 relativepermeability µxifplanar, µrifaxisymmetric
Mu2 relativepermeability µyifplanar, µzifaxisymmetric
Pe Powerdensitydissipatedthroughohmiclosses
Ph Powerdensitydissipatedby hysteresis
Example: Tocatch all valuesat (0.01,0)use
A, B1, B2, Sig, E, H1, H2, Je, Js, Mu1, Mu2, Pe, Ph = mo getpointvalues(0.01,0)
Formagnetostaticproblems,allimaginaryquantitiesare z ero.
•mo_makeplot(PlotType,NumPoints,Filename,FileFormat) Allows Lua access to the
X-Y plot routines. If only PlotType or only PlotType andNumPoints are speciﬁed, the
commandis interpreted as arequest to plottherequested plo ttypeto thescreen. If, inaddi-
tion, the Filename parameter is speciﬁed, the plot is instead written to disk to the speciﬁed
ﬁle name as an extended metaﬁle. If the FileFormat parameter is also, the command is
instead interpreted as a command to write the data to disk to t he specﬁed ﬁle name, rather
thandisplayitto makea graphicalplot. Validentries for PlotType are:
PlotType Deﬁnition
0 Potential
1 |B|
2 B·n
3 B·t
4 |H|
5 H·n
6 H·t
7 Jeddy
8 Jsource+Jeddy
Validﬁleformats are
FileFormat Deﬁnition
0 Multi-columntextwithlegend
1 Multi-columntextwithno legend
2 Mathematica-styleformatting
95

---

For example, if one wanted to plot B·nto the screen with 200 points evaluated to make the
graph, thecommandwouldbe:
momakeplot(2,200)
Ifthisplotwereto bewrittentodiskas ametaﬁle, thecomman dwouldbe:
mo_makeplot(2,200,"c:\\temp\myfile.emf")
Towritedatainsteadofaplotto disk,thecommandwouldbeof theform:
mo_makeplot(2,200,"c:\\temp\myfile.txt",0)
•mo_getprobleminfo() Returns infoon problemdescription. Returns fourvalues:
Return value Deﬁnition
1 problemtype
2 frequency in Hz
3 depth assumedforplanarproblemsin meters
4 lengthunitused todraw theproblemin meters
•mo_getcircuitproperties("circuit") Usedprimarilytoobtainimpedanceinformation
associated with circuit properties. Properties are return ed for the circuit property named
"circuit" . Threevaluesare returned bythefunction. Inorder, theser esultsare:
–current Current carried bythecircuit
–voltsVoltagedropacross thecircuit
–flux_re Circuit’sﬂux linkage
3.4.2 Selection Commands
•moseteditmode(mode) Setsthemodeofthepostprocessortopoint,contour,orarea mode.
Validentries for modeare"point","contour" ,and"area".
•moselectblock(x,y) Select theblock thatcontainspoint(x,y).
•mogroupselectblock(n) Selects alloftheblocksthatarelabeled by blocklabelstha tare
members of group n. If no number is speciﬁed ( i.e.mogroupselectblock() ), all blocks
areselected.
•moaddcontour(x,y) Adds a contour point at (x,y). If this is the ﬁrst point then it starts a
contour, if there are existing points the contour runs from t he previous point to this point.
Themoaddcontour command has the same functionality as a right-button-click contour
pointadditionwhen theprogram isrunningininteractivemo de.
•mobendcontour(angle,anglestep) Replaces the straight line formed by the last two
points in the contour by an arc that spans angledegrees. The arc is actually composed
of many straight lines, each of which is constrained to span n o more than anglestep de-
grees. The angleparameter can take on values from -180 to 180 degrees. The anglestep
parametermustbegreater thanzero. If thereare lessthan tw opointsdeﬁned in thecontour,
thiscommandisignored.
96

---

•moselectpoint(x,y) Adds a contour point at the closest input point to (x,y). If th e se-
lectedpointandapreviousselectedpointslieattheendsof anarcsegment,acontourisadded
that traces along the arcsegment. The moselectpoint command has the same functional-
ityastheleft-button-clickcontourpointselectionwhent heprogramisrunningininteractive
mode.
•moclearcontour() Clearaprevouslydeﬁned contour
•moclearblock() Clear blockselection
3.4.3 ZoomCommands
•mo_zoomnatural() Zoomtothenaturalboundariesofthegeometry.
•mo_zoomin() Zoominonelevel.
•mo_zoomout() Zoomout onelevel.
•mozoom(x1,y1,x2,y2) Zoomtothewindowdeﬁnedbylowerleftcorner(x1,y1)andupp er
rightcorner(x2,y2).
3.4.4 ViewCommands
•mo_showmesh() Show themesh.
•mo_hidemesh() Hidethemesh.
•mo_showpoints() Showthenodepointsfrom theinputgeometry.
•mo_hidepoints() Hidethenodepointsfrom theinputgeometry.
•mosmooth("flag") This function controls whether or not smoothing is applied t o theB
andHﬁelds,whicharenaturallypiece-wiseconstantovereachel ement. Setting flagequal
to"on"turns onsmoothing,andsetting flagto"off"turnsoffsmoothing.
•mo_showgrid() Show thegrid points.
•mo_hidegrid() Hidethegridpointspoints.
•mo_grid_snap("flag") Setting flagto ”on” turns on snap to grid, setting flagto"off"
turnsoffsnapto grid.
•mo_setgrid(density,"type") Change the grid spacing. The density parameter speci-
ﬁes the space between grid points, and the typeparameter is set to "cart"for cartesian
coordinatesor "polar" forpolarcoordinates.
•mo_hidedensityplot() hidestheﬂux densityplot.
•mo_showdensityplot(legend,gscale,upper_B,lower_B,ty pe)Showstheﬂuxdensity
plotwithoptions:
97

---

–legendSet to0tohidetheplotlegendor 1toshowtheplotlegend.
–gscaleSet to0foracolourdensityplotor 1foragreyscaledensityplot.
–upper_B Sets theupperdisplaylimitforthedensityplot.
–lower_B Sets thelowerdisplaylimitforthedensityplot.
–typeTypeofdensityplottodisplay. Validentriesare "bmag","breal",and"bimag"
for magnitude, real component, and imaginary component of ﬂ ux density ( B), respec-
tively; "hmag","hreal",and"himag" for magnitude,real component,and imaginary
component of ﬁeld intensity ( H); and"jmag","jreal", and"jimag" for magnitude,
real component,and imaginarycomponentofcurrent density (J).
iflegendis setto -1all parameters areignored anddefault valuesareused e.g.:
mo_showdensityplot(-1)
•mo_hidecontourplot() Hidesthecontourplot.
•mo_showcontourplot(numcontours,lower_A,upper_A,type )showsthe Acontourplot
withoptions:
–numcontours Numberof Aequipotentiallines tobeplotted.
–upper_A Upperlimitfor Acontours.
–lower_A Lowerlimitfor Acontours.
–typeChoiceof "real","imag",or"both"to showeitherthereal, imaginary ofboth
real andimaginarycomponentsofA.
Ifnumcontours is-1allparameters are ignoredand defaultvaluesare used, e.g.:
mo_showcontourplot(-1)
•moshowvectorplot(type,scalefactor) controlsthedisplayofvectorsdenotingtheﬁeld
strength and direction. The parameters taken are the typeof plot, which should be set to 0
fornovectorplot,1fortherealpartofﬂuxdensityB;2forth ereal partofﬁeldintensityH;
3fortheimaginarypartofB;4fortheimaginarypartofH;5fo rboththerealandimaginary
parts of B; and 6 for both the real and imaginary parts of H. The scalefactor determines
therelativelength of thevectors. If the scaleis set to 1, th e length ofthe vectors are chosen
so that the highestﬂux densitycorresponds to a vectorthat i s the samelength as the current
gridsizesetting.
•mominimize minimizestheactivemagneticsoutputview.
•momaximize maximizestheactivemagneticsoutputview.
•morestore restorestheactivemagneticsoutputviewfromaminimizedo rmaximizedstate.
•moresize(width,height) resizestheactivemagneticsoutputwindowclientareatowi dth
×height.
98

---

3.4.5 Miscellaneous
•moclose() Closes thecurrent post-processorinstance.
•morefreshview() Redraws thecurrent view.
•moreload() Reloads thesolutionfrom disk.
•mosavebitmap("filename") savesabitmappedscreen shotofthecurrent viewtotheﬁle
speciﬁed by "filename" . Note that if you use a path you must use two backslashes ( e.g.
"c:\\temp\\myfemmfile.fem" ). If the ﬁle name contains a space ( e.g.ﬁle names like
c:\program files\stuff )you mustenclose the ﬁle namein (extra)quotes by usinga \"
sequence. Forexample:
mo_save_bitmap("\"c:\\temp\\screenshot.bmp\"")
•mosavemetafile("filename") saves a metaﬁle screenshot of the current view to the ﬁle
speciﬁed by "filename" , subject to the printf-type formatting explained previously for
thesavebitmap command.
•moshownames(flag) Thisfunction allowtheuserto displayor hidetheblocklabe l names
on screen. To hide the block label names, flagshould be 0. To display the names, the
parametershouldbesetto 1.
•monumnodes() Returns thenumberofnodesin thein focus magneticsoutputm esh.
•monumelements() Returns thenumberofelements intheinfocus magnetsoutput mesh.
•mogetnode(n) Returns the(x,y)or(r,z)positionofthenthmeshnode.
•mogetelement(n) MOGetElement[n]returnsthefollowingproprertiesforthe nthelement:
1. Index ofﬁrst elementnode
2. Index ofsecondelement node
3. Index ofthirdelementnode
4. x (orr) coordinateoftheelement centroid
5. y (orz) coordinateoftheelementcentroid
6. element area usingthelengthunitdeﬁned fortheproblem
7. group numberassociatedwiththeelement
3.5 ElectrostaticsPreprocessorLuaCommandSet
A number of different commands are available in the preproce ssor. Two naming conventions can
beused: onewhichseparateswordsinthecommandnamesbyund erscores,andonethateliminates
theunderscores.
99

---

3.5.1 Object Add/Remove Commands
•eiaddnode(x,y) Adda newnodeatx,y
•eiaddsegment(x1,y1,x2,y2) Add a new line segment from node closest to (x1,y1) to
nodeclosest to(x2,y2)
•eiaddblocklabel(x,y) Addanew blocklabel at (x,y)
•eiaddarc(x1,y1,x2,y2,angle,maxseg) Add a new arc segment from the nearest node
to(x1,y1)tothenearest nodeto (x2,y2)withangle‘angle’d ividedinto‘maxseg’segments.
•eideleteselected Deleteallselected objects.
•eideleteselectednodes Deleteselectednodes.
•eideleteselectedlabels Deleteselected blocklabels.
•eideleteselectedsegments Deleteselected segments.
•eideleteselectedarcsegments Deleteselects arcs.
3.5.2 GeometrySelection Commands
•eiclearselected() Clear all selectednodes, blocks,segmentsand arcsegments .
•eiselectsegment(x,y) Select thelinesegmentclosestto(x,y)
•eiselectnode(x,y) Select the node closest to (x,y). Returns the coordinates of the se-
lected node.
•eiselectlabel(x,y) Select the label closet to (x,y). Returns the coordinates of the se-
lected label.
•eiselectarcsegment(x,y) Select thearc segmentclosestto (x,y)
•eiselectgroup(n) Selectthenthgroupofnodes,segments,arcsegmentsandblocklabels.
Thisfunctionwillclearallpreviouslyselectedelementsa ndleavetheeditmodein4(group)
•eiselectcircle(x,y,R,editmode) selectsobjectswithinacircleofradiusRcenteredat
(x,y). If only x, y, and R paramters are given,thecurrent edi t mode is used. If theeditmode
parameter is used, 0 denotes nodes, 2 denotes block labels, 2 denotes segments, 3 denotes
arcs, and 4 speciﬁes thatallentitytypes aretobeselected.
•eiselectrectangle(x1,y1,x2,y2,editmode) selectsobjectswithinarectangledeﬁned
bypoints(x1,y1)and(x2,y2). Ifnoeditmodeparameterissu pplied,thecurrenteditmodeis
used. If the editmode parameter is used, 0 denotes nodes, 2 de notes block labels, 2 denotes
segments,3 denotesarcs, and 4 speciﬁes thatall entitytype s areto beselected.
100

---

3.5.3 Object Labeling Commands
•eisetnodeprop("propname",groupno, "inconductor") Settheselectednodestohave
the nodal property "propname" and group number groupno. The"inconductor" string
speciﬁes which conductor the node belongs to. If the node doe sn’t belong to a named con-
ductor,thisparametercan beset to "<None>" .
•eisetblockprop("blockname", automesh, meshsize, group) Settheselectedblock
labelsto havetheproperties:
Block property "blockname" .
automesh : 0 = mesher defers to mesh size constraint deﬁned in meshsize , 1 = mesher
automaticallychoosesthemeshdensity.
meshsize : sizeconstraintonthemeshintheblockmarked by thislabel .
A memberofgroupnumber group
•eisetsegmentprop("propname", elementsize, automesh, hide , group, "inconductor",)
Set theselect segmentstohave:
Boundary property "propname"
Local elementsizealongsegmentnogreater than elementsize
automesh : 0=mesherdeferstotheelementconstraintdeﬁnedby elementsize ,1=mesher
automaticallychoosesmesh sizealong theselected segment s
hide: 0= nothiddeninpost-processor,1 ==hiddenin postprocess or
A memberofgroupnumber group
A member of the conductor speciﬁed by the string "inconductor". If the segment is not
part ofaconductor,thisparametercan bespeciﬁed as "<None>" .
•eisetarcsegmentprop(maxsegdeg, "propname", hide, group, " inconductor") Set
theselectedarc segmentsto:
Meshedwithelementsthat spanat most maxsegdeg degrees perelement
Boundary property "propname"
hide: 0= nothiddeninpost-processor,1 ==hiddenin postprocess or
A memberofgroupnumber group
A member of the conductor speciﬁed by the string "inconductor". If the segment is not
part ofaconductor,thisparametercan bespeciﬁed as "<None>" .
•eisetgroup(n) Set thegroupassociated oftheselected itemston
101

---

3.5.4 Problem Commands
•eiprobdef(units,type,precision,(depth),(minangle)) changes the problem deﬁ-
nition. The unitsparameter speciﬁes the units used for measuring length in th e problem
domain. Valid "units" entries are "inches" ,"millimeters" ,"centimeters" ,"mils",
"meters, and"micrometers" . Setproblemtype to"planar" for a 2-D planar problem,
or to"axi"for an axisymmetricproblem. The precision parameter dictates the precision
required by the solver. For example, entering 1.E-8requires the RMS of the residual to be
less than 10−8. A fourth parameter, representing the depth of the problem i n the into-the-
page direction for 2-D planar problems, can also be speciﬁed for planar problems. A sixth
parameterrepresents theminimumangleconstraintsent tot hemeshgenerator.
•eianalyze(flag) runsbelasolv to solve the problem. The flagparameter controls
whetherthe Belasolvewindowis visibleorminimized. Fora v isiblewindow,eitherspecify
novaluefor flagorspecify0. Foraminimizedwindow, flagshouldbesetto 1.
•eiloadsolution() loadsanddisplaysthesolutioncorrespondingtothecurren tgeometry.
•eisetfocus("documentname") SwitchestheelectrostaticsinputﬁleuponwhichLuacom-
mands are to act. If more than one electrostatics input ﬁle is being edited at a time, this
commandcan be used to switchbetween ﬁles so that themutiple ﬁles can beoperated upon
programmaticallyviaLua. documentname shouldcontainthenameofthedesireddocument
as itappears on thewindow’stitlebar.
•eisaveas("filename") savestheﬁlewithname "filename" . Noteifyouuseapathyou
mustusetwo backslashes e.g.c:\\temp\\myfemmfile.fee
3.5.5 MeshCommands
•eicreatemesh() runstriangletocreateamesh. Notethatthisisnotanecessa ry precursor
of performing an analysis, as eianalyze() will make sure the mesh is up to date before
runningan analysis. Thenumberofelements inthemeshispus hedback ontotheluastack.
•eishowmesh() togglestheﬂag thatshowsorhidesthemesh.
•eipurgemesh() clears themeshoutofboththescreen and memory.
3.5.6 Editing Commands
•eicopyrotate(bx, by, angle, copies, (editaction) )
bx, by–basepointforrotation
angle– angle by which the selected objects are incrementally shif ted to make each copy.
angleismeasured indegrees.
copies–numberofcopiestobeproduced from theselected objects.
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
102

---

•eicopytranslate(dx, dy, copies, (editaction))
dx,dy– distancebywhich theselected objectsare incrementallys hifted.
copies–numberofcopiestobeproduced from theselected objects.
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•micreateradius(x,y,r) turnsacornerlocatedat (x,y)intoacurveofradius r.
•eimoverotate(bx,by,shiftangle (editaction))
bx, by–basepointforrotation
shiftangle – anglein degreesby whichtheselected objectsarerotated.
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•eimovetranslate(dx,dy,(editaction))
dx,dy– distancebywhich theselected objectsare shifted.
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•eiscale(bx,by,scalefactor,(editaction))
bx, by–basepointforscaling
scalefactor –a multiplierthat determineshowmuchtheselected objects arescaled
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•eimirror(x1,y1,x2,y2,(editaction)) mirrortheselected objectsabout alinepassing
through the points (x1,y1) and(x2,y2). Valid editaction entries are 0 for nodes, 1 for
lines(segments),2 forblock labels,3for arcsegments,and 4 forgroups.
•eiseteditmode(editmode) Sets thecurrent editmodeto:
"nodes" – nodes
"segments" -linesegments
"arcsegments" -arc segments
"blocks" -block labels
"group" - selectedgroup
Thiscommandwillaffectallsubsequentusesoftheotheredi tingcommands,iftheyareused
WITHOUT the editaction parameter.
3.5.7 ZoomCommands
•eizoomnatural() zoomstoa“natural”viewwith sensibleextents.
•eizoomout() zoomsoutbyafactor of50%.
•eizoomin() zoominby afactorof200%.
•eizoom(x1,y1,x2,y2) Set the display area to be from the bottom left corner speciﬁe d by
(x1,y1)tothetoprightcorner speciﬁed by (x2,y2).
103

---

3.5.8 ViewCommands
•eishowgrid() Show thegrid points.
•eihidegrid() Hidethegridpointspoints.
•eigridsnap("flag") Setting ﬂag to ”on” turns on snap to grid, setting ﬂag to ”off” turns
offsnap togrid.
•eisetgrid(density,"type") Change the grid spacing. The density parameter speciﬁes
thespacebetween grid points,and thetypeparameter isset t o"cart"forCartesian coordi-
nates or "polar" forpolarcoordinates.
•eirefreshview() Redraws thecurrent view.
•eiminimize() minimizestheactivemagneticsinputview.
•eimaximize() maximizestheactivemagneticsinputview.
•eirestore() restores the active magnetics input view from a minimized or maximized
state.
•eiresize(width,height) resizes theactivemagnetics inputwindowclient area to wid th
×height.
3.5.9 Object Properties
•eigetmaterial("materialname") fetchesthematerialspeciﬁedby materialname from
thematerialslibrary.
•eiaddmaterial("materialname", ex, ey, qv) addsanewmaterialwithcalled "materialname"
withthematerialproperties:
exRelativepermittivityin thex-orr-direction.
eyRelativepermittivityin they-orz-direction.
qvVolumecharge densityinunitsofC/m3
•eiaddpointprop("pointpropname",Vp,qp) addsanewpointpropertyofname "pointpropname"
witheitheraspeciﬁed potential Vpapointchargedensity qpinunitsofC/m.
•eiaddboundprop("boundpropname", Vs, qs, c0, c1, BdryFormat )addsanewbound-
ary propertywithname "boundpropname"
For a “Fixed Voltage” type boundary condition, set the Vsparameter to the desired voltage
and allotherparameters tozero.
Toobtaina“Mixed”typeboundarycondition,set C1andC0asrequiredand BdryFormat to
1. Set allotherparameters tozero.
To obtain a prescribes surface charge density, set qsto the desired charge density in C/m2
and set BdryFormat to 2.
104

---

For a “Periodic” boundary condition, set BdryFormat to 3 and set all other parameters to
zero.
For an “Anti-Perodic” boundary condition, set BdryFormat to 4 set all other parameters to
zero.
•eiaddconductorprop("conductorname", Vc, qc, conductortyp e)adds a new con-
ductor property with name "conductorname" with either a prescribed voltage or a pre-
scribed total charge. Set the unused property to zero. The conductortype parameter is 0
forprescribed chargeand 1 forprescribed voltage.
•eideletematerial("materialname") deletesthematerialnamed "materialname" .
•eideleteboundprop("boundpropname") deletestheboundarypropertynamed "boundpropname" .
•eideleteconductor("conductorname") deletes theconductornamed conductorname .
•eideletepointprop("pointpropname") deletesthepointpropertynamed "pointpropname"
•eimodifymaterial("BlockName",propnum,value) This function allows for modiﬁca-
tionof a material’sproperties withoutredeﬁning theentir e material (e.g. so that current can
be modiﬁed from run to run). The material to be modiﬁed is spec iﬁed by "BlockName" .
The next parameter is the number of the property to be set. The last number is the value to
be applied to the speciﬁed property. The various properties that can be modiﬁed are listed
below:
propnum Symbol Description
0 BlockName Nameofthematerial
1 ex x (orr)directionrelativepermittivity
2 ey y (orz)directionrelativepermittivity
3 qs Volumecharge
•eimodifyboundprop("BdryName",propnum,value) This function allows for modiﬁca-
tion of a boundary property. The BC to be modiﬁed is speciﬁed b y"BdryName" . The next
parameteristhenumberofthepropertyto beset. Thelastnum beristhevaluetobeapplied
tothespeciﬁed property. Thevariousproperties thatcan be modiﬁedare listedbelow:
propnum Symbol Description
0 BdryName Nameofboundary property
1 Vs FixedVoltage
2 qs Prescribed charge density
3 c0 MixedBC parameter
4 c1 MixedBC parameter
5 BdryFormat Typeofboundarycondition:
0 = Prescribed V
1 = Mixed
2 = Surface charge density
3 = Periodic
4 = Antiperiodic
105

---

•eimodifypointprop("PointName",propnum,value) Thisfunctionallowsformodiﬁca-
tion of a point property. The point property to be modiﬁed is s peciﬁed by "PointName" .
The next parameter is the number of the property to be set. The last number is the value to
be applied to the speciﬁed property. The various properties that can be modiﬁed are listed
below:
propnum Symbol Description
0 PointName Nameofthepointproperty
1 Vp Prescribed nodal voltage
2 qp Pointcharge densityinC/m
•eimodifyconductorprop("ConductorName",propnum,value) Thisfunctionallowsfor
modiﬁcationofaconductorproperty. Theconductorpropert y to bemodiﬁedis speciﬁed by
"ConductorName" . The next parameter is the number of the property to be set. Th e last
number is the value to be applied to the speciﬁed property. Th e various properties that can
bemodiﬁedare listedbelow:
propnum Symbol Description
0 ConductorName Nameoftheconductorproperty
1 Vc Conductorvoltage
2 qc Totalconductorcharge
3 ConductorType 0 =Prescribed charge, 1 =Prescribed voltage
3.5.10 Miscellaneous
•eisavebitmap("filename") saves a bitmapped screenshot of the current view to the ﬁle
speciﬁed by "filename" , subject to the printf-type formatting explained previously for
theeisaveascommand.
•eisavemetafile("filename") saves a metaﬁle screenshot of the current view to the ﬁle
speciﬁed by "filename" , subject to the printf-type formatting explained previously for
theeisaveascommand.
•eirefreshview() Redraws thecurrent view.
•eiclose() closesthepreprocessorwindowand destroysthecurrent doc ument.
•eishownames(flag) Thisfunction allowtheuserto displayor hidetheblocklabe l names
on screen. To hide the block label names, flagshould be 0. To display the names, the
parametershouldbesetto 1.
•eireaddxf("filename") Thisfunctionimportsadxfﬁlespeciﬁed by "filename" .
•eisavedxf("filename") Thisfunctionsavesgeometryinformatoinin adxfﬁlespeciﬁ ed
by"filename" .
•eidefineouterspace(Zo,Ro,Ri) deﬁnes an axisymmetric external region to be used in
conjuction with the Kelvin Transformation method of modeli ng unbounded problems. The
Zoparameteristhez-locationoftheoriginoftheouterregion ,theRoparameteristheradius
106

---

of the outer region, and the Riparameter is the radius of the inner region ( i.e.the region
of interest). In the exterior region, the permeability vari es as a function of distance from
the origin of the external region. These parameters are nece ssary to deﬁne the permeability
variationin theexternalregion.
•eiattachouterspace() marksallselectedblocklabelsasmembersoftheexternalre gion
usedformodelingunboundedaxisymmetricproblemsviatheK elvinTransformation.
•eidetachouterspace() undeﬁnes all selected block labels as members of the externa l
regionusedformodelingunboundedaxisymmetricproblemsv iatheKelvinTransformation.
•eiattachdefault() marks the selected block label as the default block label. Th is block
labelis appliedtoany regionthathas notbeen explicitlyla beled.
•eidetachdefault() undeﬁnes thedefaultattributefortheselected blocklabel s.
•eimakeABC(n,R,x,y,bc) creates a series of circular shells that emulate the impedan ce of
an unboundeddomain (i.e. an InprovisedAsymptoticBoundar y Condition). The nparame-
ter containsthe numberofshells to be used (shouldbe betwee n 1 and 10), Ris theradius of
thesolutiondomain,and (x,y)denotesthecenterofthesolutiondomain. The bcparameter
should be speciﬁed as 0 for a Dirichlet outer edge or 1 for a Neu mann outer edge. If the
functionis called withoutall theparameters, thefunction makesup reasonablevaluesforthe-
missingparameters.
3.6 ElectrostaticsPostProcessorCommandSet
There are a numberof Lua scripting commands designed to oper ate in the postprocessor. As with
the preprocessor commands, these commands can be used with e ither the underscore naming or
withtheno-underscorenamingconvention.
3.6.1 DataExtractionCommands
•eolineintegral(type) Calculatethelineintegralforthedeﬁned contour
typeIntegral
0E·t
1D·n
2 Contourlength
3 Forcefromstress tensor
4 Torquefrom stresstensor
Thisintegralreturnseither1 or2values,dependingon thei ntegraltype, e.g.:
Fx, Fy = eo lineintegral(3)
•eoblockintegral(type) Calculateablockintegralfortheselected blocks
107

---

typeIntegral
0 Stored Energy
1 BlockCross-section
2 BlockVolume
3 Average Dovertheblock
4 Average Eovertheblock
5 WeightedStress TensorForce
6 WeightedStress TensorTorque
Returns oneortwo ﬂoatingpointvaluesas results, e.g.:
Fx, Fy = eo blockintegral(4)
•eogetpointvalues(X,Y) Getthevaluesassociatedwiththepointatx,yThereturnval ues,
inorder, are:
Symbol Deﬁnition
V Voltage
Dx x-orr-directioncomponentofdisplacement
Dy y-orz-directioncomponentofdisplacement
Ex x-orr-directioncomponentofelectricﬁeld intensity
Ey y-orz-directioncomponentofelectricﬁeld intensity
ex x-orr-directioncomponentofpermittivity
ey y-orz-directioncomponentofpermittivity
nrg electricﬁeld energy density
Example: Tocatch all valuesat (0.01,0)use
V,Dx,Dy,Ex,Ey,ex,ey,nrg= eo getpointvalues(0.01,0)
•eomakeplot(PlotType,NumPoints,Filename,FileFormat) Allows Lua access to the
X-Yplotroutines. IfonlyPlotTypeoronlyPlotTypeandNumP ointsarespeciﬁed,thecom-
mand is interpreted as a request to plot the requested plot ty pe to the screen. If, in addition,
the Filename parameter is speciﬁed, the plot is instead writ ten to disk to the speciﬁed ﬁle
name as an extended metaﬁle. If the FileFormat parameter is a lso, the command is instead
interpreted as a command to write the data to disk to the specﬁ ed ﬁle name, rather than
displayittomakeagraphical plot. ValidentriesforPlotTy peare:
PlotType Deﬁnition
0 V (Voltage)
1 |D|(Magnitude of flux density)
2 D . n (Normal flux density)
3 D . t (Tangential flux density)
4 |E|(Magnitude of field intensity)
5 E . n (Normal field intensity)
6 E . t (Tangential field intensity)
Validﬁleformats are:
108

---

FileFormat Deﬁnition
0 Multi-column text with legend
1 Multi-column text with no legend
2 Mathematica-style formatting
For example, if one wanted to plot Vto the screen with 200 points evaluated to make the
graph, thecommandwouldbe:
eomakeplot(0,200)
Ifthisplotwereto bewrittentodiskas ametaﬁle, thecomman dwouldbe:
eomakeplot(0,200,"c:temp.emf")
Towritedatainsteadofaplotto disk,thecommandwouldbeof theform:
eomakeplot(0,200,"c:temp.txt",0)
•eogetprobleminfo() Returns info on problem description. Returns three values: the
Problem type (0 for planar and 1 for axisymmetric); the depth assumed for planar problems
in units of meters; and the length unit used to draw the geomet ry represented in units of
meters.
•eogetconductorproperties("conductor") Properties are returned for the conductor
property named ”conductor”. Two values are returned: The vo ltage of the speciﬁed con-
ductor,and thechargecarried onthespeciﬁed conductor.
3.6.2 Selection Commands
•eoseteditmode(mode) Setsthemodeofthepostprocessortopoint,contour,orarea mode.
Validentries formodeare "point", "contour", and"area".
•eoselectblock(x,y) Select theblockthat containspoint (x,y).
•eogroupselectblock(n) Selectsalloftheblocksthatarelabeledbyblocklabelstha tare
members of group n. If no number is speciﬁed ( i.e.eogroupselectblock() ), all blocks
areselected.
•eoselectconductor("name") Selects all nodes, segments,and arc segmentsthat are part
of the conductor speciﬁed by the string ("name") . This command is used to select con-
ductorsforthepurposesofthe“weightedstresstensor”for ceandtorqueintegrals,wherethe
conductorsarepointsorsurfaces,ratherthanregions( i.e.can’tbeselectedwith eoselectblock ).
•eoaddcontour(x,y) Adds a contour point at (x,y). If this is the ﬁrst point then it
starts a contour, if there are existing points the contour ru ns from the previous point to this
point. The eoaddcontour command has the same functionality as a right-button-click
contourpointadditionwhen theprogramisrunningin intera ctivemode.
•eobendcontour(angle,anglestep) Replaces the straight line formed by the last two
points in the contour by an arc that spans angle degrees. The a rc is actually composed
ofmanystraightlines,eachofwhichisconstrainedtospann omorethananglestepdegrees.
109

---

Theangleparameter can takeon values from -180 to 180 degrees. The anglestep param-
eter must be greater than zero. If there are less than two poin ts deﬁned in the contour, this
commandisignored.
•eoselectpoint(x,y) Adds a contour point at the closest input point to (x,y).If the se-
lectedpointandapreviousselectedpointslieattheendsof anarcsegment,acontourisadded
thattraces alongthearcsegment. The selectpoint commandhasthesamefunctionalityas
theleft-button-clickcontourpointselectionwhenthepro gramisrunningininteractivemode.
•eoclearcontour() Clearaprevouslydeﬁned contour
•eoclearblock() Clear blockselection
3.6.3 ZoomCommands
•eozoomnatural() Zoomtothenaturalboundariesofthegeometry.
•eozoomin() Zoominonelevel.
•eozoomout() Zoomout onelevel.
•eozoom(x1,y1,x2,y2) Zoom to the window deﬁned by lower left corner (x1,y1) and
upperrightcorner (x2,y2).
3.6.4 ViewCommands
•eoshowmesh() Show themesh.
•eohidemesh() Hidethemesh.
•eoshowpoints() Showthenodepointsfrom theinputgeometry.
•eohidepoints() Hidethenodepointsfrom theinputgeometry.
•eosmooth("flag") This function controls whether or not smoothing is applied t o theD
andEﬁeldswhicharenaturallypiece-wiseconstantovereachele ment. Settingﬂagequalto
"on"turnson smoothing,and settingﬂag to "off"turnsoffsmoothing.
•eoshowgrid() Show thegrid points.
•eohidegrid() Hidethegridpointspoints.
eogridsnap("flag") Setting ﬂag to ”on” turns on snap to grid, setting ﬂag to ”off” turns
offsnap togrid.
•eosetgrid(density,"type") Change the grid spacing. The density parameter speciﬁes
thespacebetween grid points,and thetypeparameter isset t o"cart"forCartesian coordi-
nates or "polar" forpolarcoordinates.
•eohidedensityplot() hidestheﬂux densityplot.
110

---

•eoshowdensityplot(legend,gscale,type,upper D,lower D)Shows the ﬂux density
plotwithoptions:
legendSet to0 tohidetheplotlegendor1 toshowtheplotlegend.
gscaleSet to0 foracolourdensityplotor1 foragrey scaledensityp lot.
upper DSetstheupperdisplaylimitforthedensityplot.
lower DSetsthelowerdisplaylimitforthedensityplot.
typeSets the type of density plot. A value of 0 plots voltage, 1 plo ts the magnitude of D,
and 2plotsthemagnitudeof E
•eohidecontourplot() Hidesthecontourplot.
•eoshowcontourplot(numcontours,lower V,upper V)shows the Vcontour plot with
options:
numcontours Numberofequipotentiallinesto beplotted.
upper VUpperlimitforcontours.
lower VLowerlimitforcontours.
Ifeonumcontours is -1 allparameters are ignoredand defaultvaluesare used,
e.g.showcontour plot(-1)
•eoshowvectorplot(type,scalefactor) controlsthedisplayofvectorsdenotingtheﬁeld
strength and direction. The parameters taken are the typeof plot, which should be set to
0 for no vector plot, 1 for ﬂux density D, and 2 for ﬁeld intensity E. Thescalefactor
determinestherelativelengthofthevectors. Ifthescale i sset to 1, thelengthofthevectors
are chosen so that the highest ﬂux density corresponds to a ve ctorthat is the same length as
thecurrent gridsizesetting.
•eominimize() minimizestheactivemagneticsinputview.
•eomaximize() maximizestheactivemagneticsinputview.
•eorestore() restores the active magnetics input view from a minimized or maximized
state.
•eoresize(width,height) resizes theactivemagnetics inputwindowclient area to wid th
×height.
3.6.5 Miscellaneous
•eoclose() closethecurrent postprocessorwindow.
•eorefreshview() Redraws thecurrent view.
•eoreload() Reloads thesolutionfrom disk.
111

---

•eosavebitmap("filename") saves a bitmapped screen shot of the current view to the
ﬁle speciﬁed by "filename" . Note that if you use a path you must use two backslashes
(e.g."c:\\temp\\myfile.bmp" ). If the ﬁle name contains a space (e.g. ﬁle names like
c:\program ﬁles \stuff) you must enclose the ﬁle name in (extra) quotes by usin g a\"se-
quence. Forexample:
eosavebitmap(" \"c:\\temp\\screenshot.bmp \"")
•eosavemetafile("filename") saves a metaﬁle screenshot of the current view to the ﬁle
speciﬁed by "filename" , subject to the printf-type formatting explained previous ly for the
savebitmap command.
•eoshownames(flag) Thisfunction allowtheuserto displayor hidetheblocklabe l names
on screen. To hide the block label names, flagshould be 0. To display the names, the
parametershouldbesetto 1.
•eonumnodes() Returns thenumberofnodesin thein focus electrostaticsou tputmesh.
•eonumelements() Returns the number of elements in the in focus electrostatic s output
mesh.
•eogetnode(n) Returns the(x,y)or(r,z)positionofthenthmeshnode.
•eogetelement(n) MOGetElement[n]returnsthefollowingproprertiesforthe nthelement:
1. Index ofﬁrst elementnode
2. Index ofsecondelement node
3. Index ofthirdelementnode
4. x (orr) coordinateoftheelement centroid
5. y (orz) coordinateoftheelementcentroid
6. element area usingthelengthunitdeﬁned fortheproblem
7. group numberassociatedwiththeelement
3.7 HeatFlowPreprocessorLuaCommandSet
A number of different commands are available in the preproce ssor. Two naming conventions can
beused: onewhichseparateswordsinthecommandnamesbyund erscores,andonethateliminates
theunderscores.
112

---

3.7.1 Object Add/Remove Commands
•hiaddnode(x,y) Adda newnodeatx,y
•hiaddsegment(x1,y1,x2,y2) Add a new line segment from node closest to (x1,y1) to
nodeclosest to(x2,y2)
•hiaddblocklabel(x,y) Addanew blocklabel at (x,y)
•hiaddarc(x1,y1,x2,y2,angle,maxseg) Add a new arc segment from the nearest node
to(x1,y1)tothenearest nodeto (x2,y2)withangle‘angle’d ividedinto‘maxseg’segments.
•hideleteselected Deleteallselected objects.
•hideleteselectednodes Deleteselectednodes.
•hideleteselectedlabels Deleteselected blocklabels.
•hideleteselectedsegments Deleteselected segments.
•hideleteselectedarcsegments Deleteselects arcs.
3.7.2 GeometrySelection Commands
•hiclearselected() Clear all selectednodes, blocks,segmentsand arcsegments .
•hiselectsegment(x,y) Select thelinesegmentclosestto(x,y)
•hiselectnode(x,y) Select the node closest to (x,y). Returns the coordinates of the se-
lected node.
•hiselectlabel(x,y) Select the label closet to (x,y). Returns the coordinates of the se-
lected label.
•hiselectarcsegment(x,y) Select thearc segmentclosestto (x,y)
•hiselectgroup(n) Selectthenthgroupofnodes,segments,arcsegmentsandblocklabels.
Thisfunctionwillclearallpreviouslyselectedelementsa ndleavetheeditmodein4(group)
•hiselectcircle(x,y,R,editmode) selectsobjectswithinacircleofradiusRcenteredat
(x,y). If only x, y, and R paramters are given,thecurrent edi t mode is used. If theeditmode
parameter is used, 0 denotes nodes, 2 denotes block labels, 2 denotes segments, 3 denotes
arcs, and 4 speciﬁes thatallentitytypes aretobeselected.
•hiselectrectangle(x1,y1,x2,y2,editmode) selectsobjectswithinarectangledeﬁned
bypoints(x1,y1)and(x2,y2). Ifnoeditmodeparameterissu pplied,thecurrenteditmodeis
used. If the editmode parameter is used, 0 denotes nodes, 2 de notes block labels, 2 denotes
segments,3 denotesarcs, and 4 speciﬁes thatall entitytype s areto beselected.
113

---

3.7.3 Object Labeling Commands
•hisetnodeprop("propname",groupno, "inconductor") Settheselectednodestohave
the nodal property "propname" and group number groupno. The"inconductor" string
speciﬁes which conductor the node belongs to. If the node doe sn’t belong to a named con-
ductor,thisparametercan beset to "<None>" .
•hisetblockprop("blockname", automesh, meshsize, group) Settheselectedblock
labelsto havetheproperties:
Block property "blockname" .
automesh : 0 = mesher defers to mesh size constraint deﬁned in meshsize , 1 = mesher
automaticallychoosesthemeshdensity.
meshsize : sizeconstraintonthemeshintheblockmarked by thislabel .
A memberofgroupnumber group
•hisetsegmentprop("propname", elementsize, automesh, hide , group, "inconductor")
Set theselect segmentstohave:
Boundary property "propname"
Local elementsizealongsegmentnogreater than elementsize
automesh : 0=mesherdeferstotheelementconstraintdeﬁnedby elementsize ,1=mesher
automaticallychoosesmesh sizealong theselected segment s
hide: 0= nothiddeninpost-processor,1 ==hiddenin postprocess or
A memberofgroupnumber group
A member of the conductor speciﬁed by the string "inconductor". If the segment is not
part ofaconductor,thisparametercan bespeciﬁed as "<None>" .
•hisetarcsegmentprop(maxsegdeg, "propname", hide, group, " inconductor") Set
theselectedarc segmentsto:
Meshedwithelementsthat spanat most maxsegdeg degrees perelement
Boundary property "propname"
hide: 0= nothiddeninpost-processor,1 ==hiddenin postprocess or
A memberofgroupnumber group
A member of the conductor speciﬁed by the string "inconductor". If the segment is not
part ofaconductor,thisparametercan bespeciﬁed as "<None>" .
•hisetgroup(n) Set thegroupassociated oftheselected itemston
114

---

3.7.4 Problem Commands
•hiprobdef(units,type,precision,(depth),(minangle)) changes the problem deﬁ-
nition. The unitsparameter speciﬁes the units used for measuring length in th e problem
domain. Valid "units" entries are "inches" ,"millimeters" ,"centimeters" ,"mils",
"meters, and"micrometers" . Setproblemtype to"planar" for a 2-D planar problem,
or to"axi"for an axisymmetricproblem. The precision parameter dictates the precision
required by the solver. For example, entering 1.E-8requires the RMS of the residual to be
less than 10−8. A fourth parameter, representing the depth of the problem i n the into-the-
page direction for 2-D planar problems, can also be speciﬁed for planar problems. A sixth
parameterrepresents theminimumangleconstraintsent tot hemeshgenerator.
•hianalyze(flag) runshsolvtosolvetheproblem. The flagparametercontrolswhether
thehsolvewindowisvisibleorminimized. Foravisiblewind ow,eitherspecifynovaluefor
flagorspecify 0. Foraminimizedwindow, flagshouldbesetto 1.
•hiloadsolution() loadsanddisplaysthesolutioncorrespondingtothecurren tgeometry.
•hisetfocus("documentname") Switches the heat ﬂow input ﬁle upon which Lua com-
mandsaretoact. Ifmorethanoneheatﬂowinputﬁleisbeinged itedatatime,thiscommand
can be used to switch between ﬁles so that the mutipleﬁles can be operated upon program-
matically via Lua. documentname should contain the name of the desired document as it
appears on thewindow’stitlebar.
•hisaveas("filename") savestheﬁlewithname "filename" . Noteifyouuseapathyou
mustusetwo backslashes e.g.c:\\temp\\myfile.feh
3.7.5 MeshCommands
•hicreatemesh() runstriangletocreateamesh. Notethatthisisnotanecessa ry precursor
of performing an analysis, as hianalyze() will make sure the mesh is up to date before
runningan analysis. Thenumberofelements inthemeshispus hedback ontotheluastack.
•hishowmesh() togglestheﬂag thatshowsorhidesthemesh.
•hipurgemesh() clears themeshoutofboththescreen and memory.
3.7.6 Editing Commands
•hicopyrotate(bx, by, angle, copies, (editaction) )
bx, by–basepointforrotation
angle– angle by which the selected objects are incrementally shif ted to make each copy.
angleismeasured indegrees.
copies–numberofcopiestobeproduced from theselected objects.
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
115

---

•hicopytranslate(dx, dy, copies, (editaction))
dx,dy– distancebywhich theselected objectsare incrementallys hifted.
copies–numberofcopiestobeproduced from theselected objects.
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•micreateradius(x,y,r) turnsacornerlocatedat (x,y)intoacurveofradius r.
•himoverotate(bx,by,shiftangle (editaction))
bx, by–basepointforrotation
shiftangle – anglein degreesby whichtheselected objectsarerotated.
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•himovetranslate(dx,dy,(editaction))
dx,dy– distancebywhich theselected objectsare shifted.
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•hiscale(bx,by,scalefactor,(editaction))
bx, by–basepointforscaling
scalefactor –a multiplierthat determineshowmuchtheselected objects arescaled
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•himirror(x1,y1,x2,y2,(editaction)) mirrortheselected objectsabout alinepassing
through the points (x1,y1) and(x2,y2). Valid editaction entries are 0 for nodes, 1 for
lines(segments),2 forblock labels,3for arcsegments,and 4 forgroups.
•hiseteditmode(editmode) Sets thecurrent editmodeto:
"nodes" – nodes
"segments" -linesegments
"arcsegments" -arc segments
"blocks" -block labels
"group" - selectedgroup
Thiscommandwillaffectallsubsequentusesoftheotheredi tingcommands,iftheyareused
WITHOUT the editaction parameter.
3.7.7 ZoomCommands
•hizoomnatural() zoomstoa“natural”viewwith sensibleextents.
•hizoomout() zoomsoutbyafactor of50%.
•hizoomin() zoominby afactorof200%.
•hizoom(x1,y1,x2,y2) Set the display area to be from the bottom left corner speciﬁe d by
(x1,y1)tothetoprightcorner speciﬁed by (x2,y2).
116

---

3.7.8 ViewCommands
•hishowgrid() Show thegrid points.
•hihidegrid() Hidethegridpointspoints.
•higridsnap("flag") Setting ﬂag to ”on” turns on snap to grid, setting ﬂag to ”off” turns
offsnap togrid.
•hisetgrid(density,"type") Change the grid spacing. The density parameter speciﬁes
thespacebetween grid points,and thetypeparameter isset t o"cart"forCartesian coordi-
nates or "polar" forpolarcoordinates.
•hirefreshview() Redraws thecurrent view.
•himinimize() minimizestheactiveheat ﬂowinputview.
•himaximize() maximizestheactiveheat ﬂow inputview.
•hirestore() restorestheactiveheatﬂowinputviewfromaminimizedorma ximizedstate.
•hiresize(width,height) resizes the active heat ﬂow input window client area to width
×height.
3.7.9 Object Properties
•higetmaterial("materialname") fetchesthematerialspeciﬁedby materialname from
thematerialslibrary.
•hiaddmaterial("materialname", kx, ky, qv, kt) adds a new material with called
"materialname" withthematerialproperties:
kxThermal conductivityin thex-orr-direction.
kyThermal conductivityin they-orz-direction.
qvVolumeheat generation densityin unitsofW/m3.
ktVolumetricheat capacity inunitsofMJ/(m3*K).
•hiaddpointprop("pointpropname",Tp,qp) addsanewpointpropertyofname "pointpropname"
witheitheraspeciﬁed temperature Tporapointheatgenerationdensity qpinunitsofW/m.
•hiaddboundprop("boundpropname", BdryFormat, Tset, qs, Tin f, h, beta) adds
anewboundary propertywithname "boundpropname" .
–For a “Fixed Temperature” type boundary condition, set the Tsetparameter to the
desired temperatureand allotherparameters tozero.
–Toobtaina“HeatFlux”typeboundarycondition,set qstobetheheatﬂuxdensityand
BdryFormat to 1. Set allotherparameters tozero.
117

---

–Toobtainaconvectionboundarycondition,set htothedesiredheattransfercoefﬁcient
andTinfto thedesired externaltemperatureand set BdryFormat to 2.
–Fora Radiationboundarycondition,set betaequal tothedesired emissivityand Tinf
to thedesiredexternaltemperatureand set BdryFormat to3.
–Fora“Periodic”boundarycondition,set BdryFormat to4 andsetall otherparameters
to zero.
–Foran“Anti-Perodic”boundarycondition,set BdryFormat to5setallotherparameters
to zero.
•hiaddconductorprop("conductorname", Tc, qc, conductortyp e)adds a new con-
ductorpropertywithname "conductorname" witheitheraprescribedtemperatureorapre-
scribed total heat ﬂux. Set theunused property to zero. The conductortype parameter is 0
forprescribed heat ﬂux and1 forprescribed temperature.
•hideletematerial("materialname") deletesthematerialnamed "materialname" .
•hideleteboundprop("boundpropname") deletestheboundarypropertynamed "boundpropname" .
•hideleteconductor("conductorname") deletes theconductornamed conductorname .
•hideletepointprop("pointpropname") deletesthepointpropertynamed "pointpropname"
•himodifymaterial("BlockName",propnum,value) This function allows for modiﬁca-
tionof a material’sproperties withoutredeﬁning theentir e material (e.g. so that current can
be modiﬁed from run to run). The material to be modiﬁed is spec iﬁed by "BlockName" .
The next parameter is the number of the property to be set. The last number is the value to
be applied to the speciﬁed property. The various properties that can be modiﬁed are listed
below:
propnum Symbol Description
0 BlockName Nameofthematerial
1 kx x (orr)directionthermalconductivity
2 ky y (orz)directionthermalconductivity
3 qs Volumeheat generation
4 kt Volumetricheat capacity
•himodifyboundprop("BdryName",propnum,value) This function allows for modiﬁca-
tion of a boundary property. The BC to be modiﬁed is speciﬁed b y"BdryName" . The next
parameteristhenumberofthepropertyto beset. Thelastnum beristhevaluetobeapplied
tothespeciﬁed property. Thevariousproperties thatcan be modiﬁedare listedbelow:
118

---

propnum Symbol Description
0 BdryName Nameofboundary property
1 BdryFormat Typeofboundarycondition:
0 = Prescribed temperature
1 = Heat Flux
2 = Convection
3 = Radiation
4 = Periodic
5 = Antiperiodic
2 Tset FixedTemperature
3 qs Prescribed heat ﬂux density
4 Tinf Externaltemperature
5 h Heat transfercoefﬁcient
6 beta Emissivity
•himodifypointprop("PointName",propnum,value) Thisfunctionallowsformodiﬁca-
tion of a point property. The point property to be modiﬁed is s peciﬁed by "PointName" .
The next parameter is the number of the property to be set. The last number is the value to
be applied to the speciﬁed property. The various properties that can be modiﬁed are listed
below:
propnum Symbol Description
0 PointName Nameofthepointproperty
1 Tp Prescribed nodal temperature
2 qp Pointheat generation inW/m
•himodifyconductorprop("ConductorName",propnum,value) Thisfunctionallowsfor
modiﬁcationofaconductorproperty. Theconductorpropert y to bemodiﬁedis speciﬁed by
"ConductorName" . The next parameter is the number of the property to be set. Th e last
number is the value to be applied to the speciﬁed property. Th e various properties that can
bemodiﬁedare listedbelow:
propnum Symbol Description
0 ConductorName Nameoftheconductorproperty
1 Tc Conductortemperature
2 qc Totalconductorheat ﬂux
3 ConductorType 0 =Prescribed heat ﬂow,1 =Prescribed temperature
•hiaddtkpoint("materialname",T,k) adds the point (T,k)to the thermal conductivity
vs. temperaturecurveforthematerial speciﬁed by "materialname" .
•hicleartkpoints("materialname") erases all of the thermal conductivity points that
havebeen deﬁned forthematerial named "materialname" .
3.7.10 Miscellaneous
•hisavebitmap("filename") saves a bitmapped screenshot of the current view to the ﬁle
speciﬁed by "filename" , subject to the printf-type formatting explained previously for
thehisaveascommand.
119

---

•hisavemetafile("filename") saves a metaﬁle screenshot of the current view to the ﬁle
speciﬁed by "filename" , subject to the printf-type formatting explained previously for
thehisaveascommand.
•hirefreshview() Redraws thecurrent view.
•hiclose() closesthepreprocessorwindowand destroysthecurrent doc ument.
•hishownames(flag) Thisfunction allowtheuserto displayor hidetheblocklabe l names
on screen. To hide the block label names, flagshould be 0. To display the names, the
parametershouldbesetto 1.
•hireaddxf("filename") Thisfunctionimportsadxfﬁlespeciﬁed by "filename" .
•hisavedxf("filename") Thisfunctionsavesgeometryinformationin adxfﬁlespeciﬁ ed
by"filename" .
•hidefineouterspace(Zo,Ro,Ri) deﬁnes an axisymmetric external region to be used in
conjuction with the Kelvin Transformation method of modeli ng unbounded problems. The
Zoparameteristhez-locationoftheoriginoftheouterregion ,theRoparameteristheradius
of the outer region, and the Riparameter is the radius of the inner region ( i.e.the region
of interest). In the exterior region, the permeability vari es as a function of distance from
the origin of the external region. These parameters are nece ssary to deﬁne the permeability
variationin theexternalregion.
•hiattachouterspace() marksallselectedblocklabelsasmembersoftheexternalre gion
usedformodelingunboundedaxisymmetricproblemsviatheK elvinTransformation.
•hidetachouterspace() undeﬁnes all selected block labels as members of the externa l
regionusedformodelingunboundedaxisymmetricproblemsv iatheKelvinTransformation.
•hiattachdefault() marks the selected block label as the default block label. Th is block
labelis appliedtoany regionthathas notbeen explicitlyla beled.
•hidetachdefault() undeﬁnes thedefaultattributefortheselected blocklabel s.
•himakeABC(n,R,x,y,bc) creates a series of circular shells that emulate the impedan ce of
an unboundeddomain (i.e. an InprovisedAsymptoticBoundar y Condition). The nparame-
ter containsthe numberofshells to be used (shouldbe betwee n 1 and 10), Ris theradius of
thesolutiondomain,and (x,y)denotesthecenterofthesolutiondomain. The bcparameter
should be speciﬁed as 0 for a Dirichlet outer edge or 1 for a Neu mann outer edge. If the
functionis called withoutall theparameters, thefunction makesup reasonablevaluesforthe-
missingparameters.
3.8 HeatFlowPostProcessorCommandSet
There are a numberof Lua scripting commands designed to oper ate in the postprocessor. As with
the preprocessor commands, these commands can be used with e ither the underscore naming or
withtheno-underscorenamingconvention.
120

---

3.8.1 DataExtractionCommands
•holineintegral(type) Calculatethelineintegralforthedeﬁned contour
typeIntegral
0 Temperaturedifference ( G·t)
1 Heat ﬂuxthroughthecontour( F·n)
2 Contourlength
3 AverageTemperature
Thisintegralreturnseither1 or2values,dependingon thei ntegraltype, e.g.:
Ftot, Favg = ho lineintegral(2)
•hoblockintegral(type) Calculateablockintegralfortheselected blocks
typeIntegral
0 Average Tovertheblock
1 BlockCross-section
2 BlockVolume
3 Average Fovertheblock
4 Average Govertheblock
Returns oneortwo ﬂoatingpointvaluesas results, e.g.:
Gx, Gy = ho blockintegral(4)
•hogetpointvalues(X,Y) Getthevaluesassociatedwiththepointatx,yThereturnval ues,
inorder, are:
Symbol Deﬁnition
V Temperature
Fx x-orr-directioncomponentofheat ﬂux density
Fy y-orz-directioncomponentofheat ﬂux density
Gx x-orr-directioncomponentoftemperaturegradient
Gy y-orz-directioncomponentoftemperaturegradient
kx x-orr-directioncomponentofthermalconductivity
ky y-orz-directioncomponentofthermalconductivity
Example: Tocatch all valuesat (0.01,0)use
T,Fx,Fy,Gx,Gy,kx,ky= ho getpointvalues(0.01,0)
•homakeplot(PlotType,NumPoints,Filename,FileFormat) Allows Lua access to the
X-Yplotroutines. IfonlyPlotTypeoronlyPlotTypeandNumP ointsarespeciﬁed,thecom-
mand is interpreted as a request to plot the requested plot ty pe to the screen. If, in addition,
the Filename parameter is speciﬁed, the plot is instead writ ten to disk to the speciﬁed ﬁle
name as an extended metaﬁle. If the FileFormat parameter is a lso, the command is instead
interpreted as a command to write the data to disk to the specﬁ ed ﬁle name, rather than
displayittomakeagraphical plot. ValidentriesforPlotTy peare:
121

---

PlotType Deﬁnition
0 V (Temperature)
1 |D|(Magnitude of heat flux density)
2 D . n (Normal heat flux density)
3 D . t (Tangential heat flux density)
4 |E|(Magnitude of field intensity)
5 E . n (Normal field intensity)
6 E . t (Tangential field intensity)
Validﬁleformats are:
FileFormat Deﬁnition
0 Multi-column text with legend
1 Multi-column text with no legend
2 Mathematica-style formatting
For example, if one wanted to plot Vto the screen with 200 points evaluated to make the
graph, thecommandwouldbe:
homakeplot(0,200)
Ifthisplotwereto bewrittentodiskas ametaﬁle, thecomman dwouldbe:
homakeplot(0,200,"c:temp.emf")
Towritedatainsteadofaplotto disk,thecommandwouldbeof theform:
homakeplot(0,200,"c:temp.txt",0)
•hogetprobleminfo() Returns info on problem description. Returns three values: the
Problem type (0 for planar and 1 for axisymmetric); the depth assumed for planar problems
inunitsofmeters;and thelengthunitused todraw theproble min meters.
•hogetconductorproperties("conductor") Properties are returned for the conductor
property named ”conductor”. Two values are returned: The te mperature of the speciﬁed
conductor,and thetotalheatﬂux throughthespeciﬁed condu ctor.
3.8.2 Selection Commands
•hoseteditmode(mode) Setsthemodeofthepostprocessortopoint,contour,orarea mode.
Validentries formodeare "point", "contour", and"area".
•hoselectblock(x,y) Select theblockthat containspoint (x,y).
•hogroupselectblock(n) Selectsalloftheblocksthatarelabeledbyblocklabelstha tare
members of group n. If no number is speciﬁed ( i.e.hogroupselectblock() ), all blocks
areselected.
•hoselectconductor("name") Selects all nodes, segments,and arc segmentsthat are part
of the conductor speciﬁed by the string ("name") . This command is used to select con-
ductorsforthepurposesofthe“weightedstresstensor”for ceandtorqueintegrals,wherethe
conductorsarepointsorsurfaces,ratherthanregions( i.e.can’tbeselectedwith hoselectblock ).
122

---

•hoaddcontour(x,y) Adds a contour point at (x,y). If this is the ﬁrst point then it
starts a contour, if there are existing points the contour ru ns from the previous point to this
point. The hoaddcontour command has the same functionality as a right-button-click
contourpointadditionwhen theprogramisrunningin intera ctivemode.
•hobendcontour(angle,anglestep) Replaces the straight line formed by the last two
points in the contour by an arc that spans angle degrees. The a rc is actually composed
ofmanystraightlines,eachofwhichisconstrainedtospann omorethananglestepdegrees.
Theangleparameter can takeon values from -180 to 180 degrees. The anglestep param-
eter must be greater than zero. If there are less than two poin ts deﬁned in the contour, this
commandisignored.
•hoselectpoint(x,y) Adds a contour point at the closest input point to (x,y).If the se-
lectedpointandapreviousselectedpointslieattheendsof anarcsegment,acontourisadded
thattraces alongthearcsegment. The selectpoint commandhasthesamefunctionalityas
theleft-button-clickcontourpointselectionwhenthepro gramisrunningininteractivemode.
•hoclearcontour() Clearaprevouslydeﬁned contour
•hoclearblock() Clear blockselection
3.8.3 ZoomCommands
•hozoomnatural() Zoomtothenaturalboundariesofthegeometry.
•hozoomin() Zoominonelevel.
•hozoomout() Zoomout onelevel.
•hozoom(x1,y1,x2,y2) Zoom to the window deﬁned by lower left corner (x1,y1) and
upperrightcorner (x2,y2).
3.8.4 ViewCommands
•hoshowmesh() Show themesh.
•hohidemesh() Hidethemesh.
•hoshowpoints() Showthenodepointsfrom theinputgeometry.
•hohidepoints() Hidethenodepointsfrom theinputgeometry.
•hosmooth("flag") This function controls whether or not smoothing is applied t o theF
andGﬁelds which are naturally piece-wise constant over each ele ment. Setting ﬂag equal
to"on"turns onsmoothing,andsettingﬂag to "off"turnsoffsmoothing.
•hoshowgrid() Show thegrid points.
123

---

•hohidegrid() Hidethegridpointspoints.
hogridsnap("flag") Setting ﬂag to ”on” turns on snap to grid, setting ﬂag to ”off” turns
offsnap togrid.
•hosetgrid(density,"type") Change the grid spacing. The density parameter speciﬁes
thespacebetween grid points,and thetypeparameter isset t o"cart"forCartesian coordi-
nates or "polar" forpolarcoordinates.
•hohidedensityplot() hidestheheat ﬂux densityplot.
•hoshowdensityplot(legend,gscale,type,upper,lower) Shows the heat ﬂux density
plotwithoptions:
legendSet to0 tohidetheplotlegendor1 toshowtheplotlegend.
gscaleSet to0 foracolourdensityplotor1 foragrey scaledensityp lot.
upperSets theupperdisplaylimitforthedensityplot.
lowerSets thelowerdisplaylimitforthedensityplot.
typeSets the type of density plot. A value of 0 plots temperature, 1 plots the magnitudeof
F, and 2plotsthemagnitudeof G
•hohidecontourplot() Hidesthecontourplot.
•hoshowcontourplot(numcontours,lower V,upper V)shows the Vcontour plot with
options:
numcontours Numberofequipotentiallinesto beplotted.
upper VUpperlimitforcontours.
lower VLowerlimitforcontours.
Ifhonumcontours is -1 allparameters are ignoredand defaultvaluesare used,
e.g.showcontour plot(-1)
•hoshowvectorplot(type,scalefactor) controlsthedisplayofvectorsdenotingtheﬁeld
strengthanddirection. Theparameterstakenarethe typeofplot,whichshouldbesetto0for
novectorplot,1forheatﬂuxdensity F,and2fortemperaturegradient G. Thescalefactor
determinestherelativelengthofthevectors. Ifthescale i sset to 1, thelengthofthevectors
are chosen so that the highest ﬂux density corresponds to a ve ctorthat is the same length as
thecurrent gridsizesetting.
•hominimize() minimizestheactiveheat ﬂowinputview.
•homaximize() maximizestheactiveheat ﬂow inputview.
•horestore() restorestheactiveheatﬂowinputviewfromaminimizedorma ximizedstate.
•horesize(width,height) resizes the active heat ﬂow input window client area to width
×height.
124

---

3.8.5 Miscellaneous
•hoclose() closethecurrent postprocessorwindow.
•horefreshview() Redraws thecurrent view.
•horeload() Reloads thesolutionfrom disk.
•hosavebitmap("filename") saves a bitmapped screen shot of the current view to the
ﬁle speciﬁed by "filename" . Note that if you use a path you must use two backslashes
(e.g."c:\\temp\\myfile.bmp" ). If the ﬁle name contains a space (e.g. ﬁle names like
c:\program ﬁles \stuff) you must enclose the ﬁle name in (extra) quotes by usin g a\"se-
quence. Forexample:
hosavebitmap(" \"c:\\temp\\screenshot.bmp \"")
•hosavemetafile("filename") saves a metaﬁle screenshot of the current view to the ﬁle
speciﬁed by "filename" , subject to the printf-type formatting explained previous ly for the
savebitmap command.
•hoshownames(flag) Thisfunction allowtheuserto displayor hidetheblocklabe l names
on screen. To hide the block label names, flagshould be 0. To display the names, the
parametershouldbesetto 1.
•honumnodes() Returns thenumberofnodesin thein focus heatﬂow outputmes h.
•honumelements() Returns thenumberofelements intheinfocus heat ﬂowoutput mesh.
•hogetnode(n) Returns the(x,y)or(r,z)positionofthenthmeshnode.
•hogetelement(n) MOGetElement[n]returnsthefollowingproprertiesforthe nthelement:
1. Index ofﬁrst elementnode
2. Index ofsecondelement node
3. Index ofthirdelementnode
4. x (orr) coordinateoftheelement centroid
5. y (orz) coordinateoftheelementcentroid
6. element area usingthelengthunitdeﬁned fortheproblem
7. group numberassociatedwiththeelement
3.9 CurrentFlowPreprocessorLuaCommandSet
A number of different commands are available in the preproce ssor. Two naming conventions can
beused: onewhichseparateswordsinthecommandnamesbyund erscores,andonethateliminates
theunderscores.
125

---

3.9.1 Object Add/Remove Commands
•ciaddnode(x,y) Adda newnodeatx,y
•ciaddsegment(x1,y1,x2,y2) Add a new line segment from node closest to (x1,y1) to
nodeclosest to(x2,y2)
•ciaddblocklabel(x,y) Addanew blocklabel at (x,y)
•ciaddarc(x1,y1,x2,y2,angle,maxseg) Add a new arc segment from the nearest node
to(x1,y1)tothenearest nodeto (x2,y2)withangle‘angle’d ividedinto‘maxseg’segments.
•cideleteselected Deleteallselected objects.
•cideleteselectednodes Deleteselectednodes.
•cideleteselectedlabels Deleteselected blocklabels.
•cideleteselectedsegments Deleteselected segments.
•cideleteselectedarcsegments Deleteselects arcs.
3.9.2 GeometrySelection Commands
•ciclearselected() Clear all selectednodes, blocks,segmentsand arcsegments .
•ciselectsegment(x,y) Select thelinesegmentclosestto(x,y)
•ciselectnode(x,y) Select the node closest to (x,y). Returns the coordinates of the se-
lected node.
•ciselectlabel(x,y) Select the label closet to (x,y). Returns the coordinates of the se-
lected label.
•ciselectarcsegment(x,y) Select thearc segmentclosestto (x,y)
•ciselectgroup(n) Selectthenthgroupofnodes,segments,arcsegmentsandblocklabels.
Thisfunctionwillclearallpreviouslyselectedelementsa ndleavetheeditmodein4(group)
•ciselectcircle(x,y,R,editmode) selectsobjectswithinacircleofradiusRcenteredat
(x,y). If only x, y, and R paramters are given,thecurrent edi t mode is used. If theeditmode
parameter is used, 0 denotes nodes, 2 denotes block labels, 2 denotes segments, 3 denotes
arcs, and 4 speciﬁes thatallentitytypes aretobeselected.
•ciselectrectangle(x1,y1,x2,y2,editmode) selectsobjectswithinarectangledeﬁned
bypoints(x1,y1)and(x2,y2). Ifnoeditmodeparameterissu pplied,thecurrenteditmodeis
used. If the editmode parameter is used, 0 denotes nodes, 2 de notes block labels, 2 denotes
segments,3 denotesarcs, and 4 speciﬁes thatall entitytype s areto beselected.
126

---

3.9.3 Object Labeling Commands
•cisetnodeprop("propname",groupno, "inconductor") Settheselectednodestohave
the nodal property "propname" and group number groupno. The"inconductor" string
speciﬁes which conductor the node belongs to. If the node doe sn’t belong to a named con-
ductor,thisparametercan beset to "<None>" .
•cisetblockprop("blockname", automesh, meshsize, group) Settheselectedblock
labelsto havetheproperties:
Block property "blockname" .
automesh : 0 = mesher defers to mesh size constraint deﬁned in meshsize , 1 = mesher
automaticallychoosesthemeshdensity.
meshsize : sizeconstraintonthemeshintheblockmarked by thislabel .
A memberofgroupnumber group
•cisetsegmentprop("propname", elementsize, automesh, hide , group, "inconductor",)
Set theselect segmentstohave:
Boundary property "propname"
Local elementsizealongsegmentnogreater than elementsize
automesh : 0=mesherdeferstotheelementconstraintdeﬁnedby elementsize ,1=mesher
automaticallychoosesmesh sizealong theselected segment s
hide: 0= nothiddeninpost-processor,1 ==hiddenin postprocess or
A memberofgroupnumber group
A member of the conductor speciﬁed by the string "inconductor". If the segment is not
part ofaconductor,thisparametercan bespeciﬁed as "<None>" .
•cisetarcsegmentprop(maxsegdeg, "propname", hide, group, " inconductor") Set
theselectedarc segmentsto:
Meshedwithelementsthat spanat most maxsegdeg degrees perelement
Boundary property "propname"
hide: 0= nothiddeninpost-processor,1 ==hiddenin postprocess or
A memberofgroupnumber group
A member of the conductor speciﬁed by the string "inconductor". If the segment is not
part ofaconductor,thisparametercan bespeciﬁed as "<None>" .
•cisetgroup(n) Set thegroupassociated oftheselected itemston
127

---

3.9.4 Problem Commands
•ciprobdef(units,type,frequency,precision,(depth),(min angle))changestheprob-
lem deﬁnition. The unitsparameter speciﬁes the units used for measuring length in th e
problem domain. Valid "units" entries are "inches" ,"millimeters" ,"centimeters" ,
"mils","meters, and"micrometers" . Setproblemtype to"planar" for a 2-D planar
problem, or to "axi"for an axisymmetric problem. The frequency parameter speciﬁes
the frequency in Hz at which the analysis ois to be performed. Theprecision parame-
ter dictates the precision required by the solver. For examp le, entering 1.E-8requires the
RMS of the residual to be less than 10−8. A fourth parameter, representing the depth of the
problemintheinto-the-pagedirectionfor2-Dplanarprobl ems,canalsobespeciﬁedforpla-
nar problems. A sixth parameter represents the minimum angl e constraint sent to the mesh
generator.
•cianalyze(flag) runsbelasolv to solve the problem. The flagparameter controls
whetherthe Belasolvewindowis visibleorminimized. Fora v isiblewindow,eitherspecify
novaluefor flagorspecify0. Foraminimizedwindow, flagshouldbesetto 1.
•ciloadsolution() loadsanddisplaysthesolutioncorrespondingtothecurren tgeometry.
•cisetfocus("documentname") SwitchestheelectrostaticsinputﬁleuponwhichLuacom-
mands are to act. If more than one electrostatics input ﬁle is being edited at a time, this
commandcan be used to switchbetween ﬁles so that themutiple ﬁles can beoperated upon
programmaticallyviaLua. documentname shouldcontainthenameofthedesireddocument
as itappears on thewindow’stitlebar.
•cisaveas("filename") savestheﬁlewithname "filename" . Noteifyouuseapathyou
mustusetwo backslashes e.g.c:\\temp\\myfemmfile.fee
3.9.5 MeshCommands
•cicreatemesh() runstriangletocreateamesh. Notethatthisisnotanecessa ry precursor
of performing an analysis, as cianalyze() will make sure the mesh is up to date before
runningan analysis. Thenumberofelements inthemeshispus hedback ontotheluastack.
•cishowmesh() togglestheﬂag thatshowsorhidesthemesh.
•cipurgemesh() clears themeshoutofboththescreen and memory.
3.9.6 Editing Commands
•cicopyrotate(bx, by, angle, copies, (editaction) )
bx, by–basepointforrotation
angle– angle by which the selected objects are incrementally shif ted to make each copy.
angleismeasured indegrees.
copies–numberofcopiestobeproduced from theselected objects.
128

---

editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•cicopytranslate(dx, dy, copies, (editaction))
dx,dy– distancebywhich theselected objectsare incrementallys hifted.
copies–numberofcopiestobeproduced from theselected objects.
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•micreateradius(x,y,r) turnsacornerlocatedat (x,y)intoacurveofradius r.
•cimoverotate(bx,by,shiftangle (editaction))
bx, by–basepointforrotation
shiftangle – anglein degreesby whichtheselected objectsarerotated.
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•cimovetranslate(dx,dy,(editaction))
dx,dy– distancebywhich theselected objectsare shifted.
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•ciscale(bx,by,scalefactor,(editaction))
bx, by–basepointforscaling
scalefactor –a multiplierthat determineshowmuchtheselected objects arescaled
editaction 0 –nodes,1– lines(segments),2–blocklabels, 3– arc segmen ts,4-group
•cimirror(x1,y1,x2,y2,(editaction)) mirrortheselected objectsabout alinepassing
through the points (x1,y1) and(x2,y2). Valid editaction entries are 0 for nodes, 1 for
lines(segments),2 forblock labels,3for arcsegments,and 4 forgroups.
•ciseteditmode(editmode) Sets thecurrent editmodeto:
"nodes" – nodes
"segments" -linesegments
"arcsegments" -arc segments
"blocks" -block labels
"group" - selectedgroup
Thiscommandwillaffectallsubsequentusesoftheotheredi tingcommands,iftheyareused
WITHOUT the editaction parameter.
129

---

3.9.7 ZoomCommands
•cizoomnatural() zoomstoa“natural”viewwith sensibleextents.
•cizoomout() zoomsoutbyafactor of50%.
•cizoomin() zoominby afactorof200%.
•cizoom(x1,y1,x2,y2) Set the display area to be from the bottom left corner speciﬁe d by
(x1,y1)tothetoprightcorner speciﬁed by (x2,y2).
3.9.8 ViewCommands
•cishowgrid() Show thegrid points.
•cihidegrid() Hidethegridpointspoints.
•cigridsnap("flag") Setting ﬂag to ”on” turns on snap to grid, setting ﬂag to ”off” turns
offsnap togrid.
•cisetgrid(density,"type") Change the grid spacing. The density parameter speciﬁes
thespacebetween grid points,and thetypeparameter isset t o"cart"forCartesian coordi-
nates or "polar" forpolarcoordinates.
•cirefreshview() Redraws thecurrent view.
•ciminimize() minimizestheactivemagneticsinputview.
•cimaximize() maximizestheactivemagneticsinputview.
•cirestore() restores the active magnetics input view from a minimized or maximized
state.
•ciresize(width,height) resizes theactivemagnetics inputwindowclient area to wid th
×height.
3.9.9 Object Properties
•cigetmaterial("materialname") fetchesthematerialspeciﬁedby materialname from
thematerialslibrary.
•ciaddmaterial("materialname", ox, oy, ex, ey, ltx, lty) adds a new material
withcalled "materialname" withthematerialproperties:
oxElectrical conductivityinthex-orr-direction inunitsof S/m.
oyElectrical conductivityinthey-orz-direction inunitsof S/m.
exRelativepermittivityin thex-orr-direction.
eyRelativepermittivityin they-orz-direction.
130

---

ltxDielectriclosstangentinthex-orr-direction.
ltyDielectriclosstangentinthey-orz-direction.
•ciaddpointprop("pointpropname",Vp,qp) addsanewpointpropertyofname "pointpropname"
witheitheraspeciﬁed potential Vpapointcurrent density qpinunitsofA/m.
•ciaddboundprop("boundpropname", Vs, qs, c0, c1, BdryFormat )addsanewbound-
ary propertywithname "boundpropname"
For a “Fixed Voltage” type boundary condition, set the Vsparameter to the desired voltage
and allotherparameters tozero.
Toobtaina“Mixed”typeboundarycondition,set C1andC0asrequiredand BdryFormat to
1. Set allotherparameters tozero.
To obtain a prescribes surface current density, set qsto the desired current density in A/m2
and set BdryFormat to 2.
For a “Periodic” boundary condition, set BdryFormat to 3 and set all other parameters to
zero.
For an “Anti-Perodic” boundary condition, set BdryFormat to 4 set all other parameters to
zero.
•ciaddconductorprop("conductorname", Vc, qc, conductortyp e)adds a new con-
ductor property with name "conductorname" with either a prescribed voltage or a pre-
scribed total current. Set the unused property to zero. The conductortype parameter is 0
forprescribed current and 1forprescribed voltage.
•cideletematerial("materialname") deletesthematerialnamed "materialname" .
•cideleteboundprop("boundpropname") deletestheboundarypropertynamed "boundpropname" .
•cideleteconductor("conductorname") deletes theconductornamed conductorname .
•cideletepointprop("pointpropname") deletesthepointpropertynamed "pointpropname"
•cimodifymaterial("BlockName",propnum,value) This function allows for modiﬁca-
tionof a material’sproperties withoutredeﬁning theentir e material (e.g. so that current can
be modiﬁed from run to run). The material to be modiﬁed is spec iﬁed by "BlockName" .
The next parameter is the number of the property to be set. The last number is the value to
be applied to the speciﬁed property. The various properties that can be modiﬁed are listed
below:
propnum Symbol Description
0 BlockName Nameofthematerial
1 ox x (orr)directionconductivity
2 oy y (orz)directionconductivity
3 ex x (orr)directionrelativepermittivity
4 ey y (orz)directionrelativepermittivity
5 ltx x (orr)directiondielectriclosstangent
6 lty y (orz)directiondielectriclosstangent
131

---

•cimodifyboundprop("BdryName",propnum,value) This function allows for modiﬁca-
tion of a boundary property. The BC to be modiﬁed is speciﬁed b y"BdryName" . The next
parameteristhenumberofthepropertyto beset. Thelastnum beristhevaluetobeapplied
tothespeciﬁed property. Thevariousproperties thatcan be modiﬁedare listedbelow:
propnum Symbol Description
0 BdryName Nameofboundary property
1 Vs FixedVoltage
2 qs Prescribed current density
3 c0 MixedBC parameter
4 c1 MixedBC parameter
5 BdryFormat Typeofboundarycondition:
0 = Prescribed V
1 = Mixed
2 = Surface current density
3 = Periodic
4 = Antiperiodic
•cimodifypointprop("PointName",propnum,value) Thisfunctionallowsformodiﬁca-
tion of a point property. The point property to be modiﬁed is s peciﬁed by "PointName" .
The next parameter is the number of the property to be set. The last number is the value to
be applied to the speciﬁed property. The various properties that can be modiﬁed are listed
below:
propnum Symbol Description
0 PointName Nameofthepointproperty
1 Vp Prescribed nodal voltage
2 qp Pointcurrent densityinA/m
•cimodifyconductorprop("ConductorName",propnum,value) Thisfunctionallowsfor
modiﬁcationofaconductorproperty. Theconductorpropert y to bemodiﬁedis speciﬁed by
"ConductorName" . The next parameter is the number of the property to be set. Th e last
number is the value to be applied to the speciﬁed property. Th e various properties that can
bemodiﬁedare listedbelow:
propnum Symbol Description
0 ConductorName Nameoftheconductorproperty
1 Vc Conductorvoltage
2 qc Totalconductorcurrent
3 ConductorType 0 =Prescribed current, 1 =Prescribed voltage
3.9.10 Miscellaneous
•cisavebitmap("filename") saves a bitmapped screenshot of the current view to the ﬁle
speciﬁed by "filename" , subject to the printf-type formatting explained previously for
thecisaveascommand.
•cisavemetafile("filename") saves a metaﬁle screenshot of the current view to the ﬁle
132

---

speciﬁed by "filename" , subject to the printf-type formatting explained previously for
thecisaveascommand.
•cirefreshview() Redraws thecurrent view.
•ciclose() closesthepreprocessorwindowand destroysthecurrent doc ument.
•cishownames(flag) Thisfunction allowtheuserto displayor hidetheblocklabe l names
on screen. To hide the block label names, flagshould be 0. To display the names, the
parametershouldbesetto 1.
•cireaddxf("filename") Thisfunctionimportsadxfﬁlespeciﬁed by "filename" .
•cisavedxf("filename") Thisfunctionsavesgeometryinformationin adxfﬁlespeciﬁ ed
by"filename" .
•cidefineouterspace(Zo,Ro,Ri) deﬁnes an axisymmetric external region to be used in
conjuction with the Kelvin Transformation method of modeli ng unbounded problems. The
Zoparameteristhez-locationoftheoriginoftheouterregion ,theRoparameteristheradius
of the outer region, and the Riparameter is the radius of the inner region ( i.e.the region
of interest). In the exterior region, the permeability vari es as a function of distance from
the origin of the external region. These parameters are nece ssary to deﬁne the permeability
variationin theexternalregion.
•ciattachouterspace() marksallselectedblocklabelsasmembersoftheexternalre gion
usedformodelingunboundedaxisymmetricproblemsviatheK elvinTransformation.
•cidetachouterspace() undeﬁnes all selected block labels as members of the externa l
regionusedformodelingunboundedaxisymmetricproblemsv iatheKelvinTransformation.
•ciattachdefault() marks the selected block label as the default block label. Th is block
labelis appliedtoany regionthathas notbeen explicitlyla beled.
•cidetachdefault() undeﬁnes thedefaultattributefortheselected blocklabel s.
•cimakeABC(n,R,x,y,bc) creates a series of circular shells that emulate the impedan ce of
anunboundeddomain(i.e. anInprovisedAsymptoticBoundar yCondition). The nparameter
containsthenumberofshellstobeused(shouldbebetween1 a nd 10), Ristheradius ofthe
solution domain, and (x,y)denotes the center of the solution domain. The bcparameter
should be speciﬁed as 0 for a Dirichlet outer edge or 1 for a Neu mann outer edge. If the
functioniscalledwithoutalltheparameters,thefunction makesupreasonablevaluesforthe
missingparameters.
3.10 CurrentFlowPostProcessorCommandSet
There are a numberof Lua scripting commands designed to oper ate in the postprocessor. As with
the preprocessor commands, these commands can be used with e ither the underscore naming or
withtheno-underscorenamingconvention.
133

---

3.10.1 Data ExtractionCommands
•colineintegral(type) Calculatethelineintegralforthedeﬁned contour
typeIntegral
0E·t
1J·n
2 Contourlength
3 Averagevoltageovercontour
4 Forcefromstress tensor
5 Torquefrom stresstensor
Thisintegralreturnseither1 or2values,dependingon thei ntegraltype, e.g.:
Fx, Fy = co lineintegral(4)
•coblockintegral(type) Calculateablockintegralfortheselected blocks
typeIntegral
0 Real Power
1 ReactivePower
2 ApparentPower
3 Time-AverageStored Energy
4 Blockcross-section area
5 Blockvolume
6 x(orr) directionWeightedStress Tensorforce, DCcompone nt
7 y(orz) directionWeightedStress Tensorforce, DCcompone nt
8 x(orr) directionWeightedStress Tensorforce, 2xfrequen cy component
9 y(orz) directionWeightedStress Tensorforce, 2xfrequen cy component
10 WeightedStress Tensortorque, DCcomponent
11 WeightedStress Tensortorque, 2xfrequency component
Returns avaluethatcan becomplex,as necessary.
•cogetpointvalues(X,Y) Getthevaluesassociatedwiththepointatx,yThereturnval ues,
inorder, are:
134

---

Symbol Deﬁnition
V Voltage
Jx x-orr-directioncomponentofcurrent density
Jy y-orz-directioncomponentofcurrent density
Kx x-orr-directioncomponentofACconductivity
Ky y-orz-directioncomponentofACconductivity
Ex x-orr-directioncomponentofelectricﬁeld intensity
Ey y-orz-directioncomponentofelectricﬁeld intensity
ex x-orr-directioncomponentofpermittivity
ey y-orz-directioncomponentofpermittivity
Jdx x-orr-directioncomponentofdisplacementcurrent densit y
Jdy y-orz-directioncomponentofdisplacementcurrent densit y
ox x-orr-directioncomponentofpermittivity
oy y-orz-directioncomponentofpermittivity
Jcx x-orr-directioncomponentofconductioncurrent density
Jcy y-orz-directioncomponentofconductioncurrent density
•comakeplot(PlotType,NumPoints,Filename,FileFormat) Allows Lua access to the
X-Yplotroutines. IfonlyPlotTypeoronlyPlotTypeandNumP ointsarespeciﬁed,thecom-
mand is interpreted as a request to plot the requested plot ty pe to the screen. If, in addition,
the Filename parameter is speciﬁed, the plot is instead writ ten to disk to the speciﬁed ﬁle
name as an extended metaﬁle. If the FileFormat parameter is a lso, the command is instead
interpreted as a command to write the data to disk to the specﬁ ed ﬁle name, rather than
displayittomakeagraphical plot. ValidentriesforPlotTy peare:
PlotType Deﬁnition
0 V (Voltage)
1 |J|(Magnitude of current density)
2 J . n (Normal current density)
3 J . t (Tangential current density)
4 |E|(Magnitude of field intensity)
5 E . n (Normal field intensity)
6 E . t (Tangential field intensity)
7 |Jc|(Magnitude of conduction current density)
8 Jc . n (Normal conduction current density)
9 Jc . t (Tangential conduction current density)
10 |Jd|(Magnitude of displacement current density)
11 Jd . n (Normal displacement current density)
12 Jd . t (Tangential displacement current density)
Validﬁleformats are:
FileFormat Deﬁnition
0 Multi-column text with legend
1 Multi-column text with no legend
2 Mathematica-style formatting
For example, if one wanted to plot Vto the screen with 200 points evaluated to make the
135

---

graph, thecommandwouldbe:
comakeplot(0,200)
Ifthisplotwereto bewrittentodiskas ametaﬁle, thecomman dwouldbe:
comakeplot(0,200,"c:temp.emf")
Towritedatainsteadofaplotto disk,thecommandwouldbeof theform:
comakeplot(0,200,"c:temp.txt",0)
•cogetprobleminfo() Returns infoon problemdescription. Returns fourvalues:
Return value Deﬁnition
1 problemtype
2 frequencyin Hz
3 depthassumedforplanarproblemsinmeters.
4 lengthunitusedto drawtheproblem,represented inmeters
•cogetconductorproperties("conductor") Properties are returned for the conductor
property named ”conductor”. Two values are returned: The vo ltage of the speciﬁed con-
ductor,and thecurrent onthespeciﬁed conductor.
3.10.2 Selection Commands
•coseteditmode(mode) Setsthemodeofthepostprocessortopoint,contour,orarea mode.
Validentries formodeare "point", "contour", and"area".
•coselectblock(x,y) Select theblockthat containspoint (x,y).
•cogroupselectblock(n) Selectsalloftheblocksthatarelabeledbyblocklabelstha tare
members of group n. If no number is speciﬁed ( i.e.cogroupselectblock() ), all blocks
areselected.
•coselectconductor("name") Selects all nodes, segments,and arc segmentsthat are part
of the conductor speciﬁed by the string ("name") . This command is used to select con-
ductorsforthepurposesofthe“weightedstresstensor”for ceandtorqueintegrals,wherethe
conductorsarepointsorsurfaces,ratherthanregions( i.e.can’tbeselectedwith coselectblock ).
•coaddcontour(x,y) Adds a contour point at (x,y). If this is the ﬁrst point then it
starts a contour, if there are existing points the contour ru ns from the previous point to this
point. The coaddcontour command has the same functionality as a right-button-click
contourpointadditionwhen theprogramisrunningin intera ctivemode.
•cobendcontour(angle,anglestep) Replaces the straight line formed by the last two
points in the contour by an arc that spans angle degrees. The a rc is actually composed
ofmanystraightlines,eachofwhichisconstrainedtospann omorethananglestepdegrees.
Theangleparameter can takeon values from -180 to 180 degrees. The anglestep param-
eter must be greater than zero. If there are less than two poin ts deﬁned in the contour, this
commandisignored.
136

---

•coselectpoint(x,y) Adds a contour point at the closest input point to (x,y).If the se-
lectedpointandapreviousselectedpointslieattheendsof anarcsegment,acontourisadded
thattraces alongthearcsegment. The selectpoint commandhasthesamefunctionalityas
theleft-button-clickcontourpointselectionwhenthepro gramisrunningininteractivemode.
•coclearcontour() Clearaprevouslydeﬁned contour
•coclearblock() Clear blockselection
3.10.3 ZoomCommands
•cozoomnatural() Zoomtothenaturalboundariesofthegeometry.
•cozoomin() Zoominonelevel.
•cozoomout() Zoomout onelevel.
•cozoom(x1,y1,x2,y2) Zoom to the window deﬁned by lower left corner (x1,y1) and
upperrightcorner (x2,y2).
3.10.4 View Commands
•coshowmesh() Show themesh.
•cohidemesh() Hidethemesh.
•coshowpoints() Showthenodepointsfrom theinputgeometry.
•cohidepoints() Hidethenodepointsfrom theinputgeometry.
•cosmooth("flag") This function controls whether or not smoothing is applied t o theD
andEﬁeldswhicharenaturallypiece-wiseconstantovereachele ment. Settingﬂagequalto
"on"turnson smoothing,and settingﬂag to "off"turnsoffsmoothing.
•coshowgrid() Show thegrid points.
•cohidegrid() Hidethegridpointspoints.
cogridsnap("flag") Setting ﬂag to ”on” turns on snap to grid, setting ﬂag to ”off” turns
offsnap togrid.
•cosetgrid(density,"type") Change the grid spacing. The density parameter speciﬁes
thespacebetween grid points,and thetypeparameter isset t o"cart"forCartesian coordi-
nates or "polar" forpolarcoordinates.
•cohidedensityplot() hidesthecurrent densityplot.
137

---

•coshowdensityplot(legend,gscale,type,upper,lower) Showsthecurrentdensityplot
withoptions:
legendSet to0 tohidetheplotlegendor1 toshowtheplotlegend.
gscaleSet to0 foracolourdensityplotor1 foragrey scaledensityp lot.
upperSets theupperdisplaylimitforthedensityplot.
lowerSets thelowerdisplaylimitforthedensityplot.
typeSets thetypeofdensityplot. Speciﬁcchoices forthetypeof densityplotinclude:
typeDescription
0|V|
1|Re(V)|
2|Im(V)|
3|J|
4|Re(J)|
5|Im(J)|
6|E|
7|Re(E)|
8|Im(E)|
•cohidecontourplot() Hidesthecontourplot.
•coshowcontourplot(numcontours,lower V,upper V),type shows the Vcontour plot
withoptions:
numcontours Numberofequipotentiallinesto beplotted;
upper VUpperlimitforcontours;
lower VLowerlimitforcontours;
typethetypeofcontourplotto berendered.
Ifconumcontours is -1 allparameters are ignoredand defaultvaluesare used,
e.g.showcontour plot(-1)
The type can take on the values of "real","imag", or"both", denoting the real part of
voltage,theimaginarypartofvoltage,orbothcomponentso fvoltage.
•coshowvectorplot(type,scalefactor) controlsthedisplayofvectorsdenotingtheﬁeld
strengthand direction. The typeparameter can takeonthefollowingvalues:
typeDescription
0 Novectorplot
1 Re (J)
2 Re (E)
3 Im (J)
4 Im (E)
5 Re (J)andIm(J)
6 Re (E)andIm(E)Thescalefactor determinestherelativelengthofthevectors.
138

---

Ifthescaleissetto1,thelengthofthevectorsarechosenso thatthehighestﬁeldmagnitude
correspondsto avectorthatis thesamelengthas thecurrent gridsizesetting.
•cominimize() minimizestheactivemagneticsinputview.
•comaximize() maximizestheactivemagneticsinputview.
•corestore() restores the active magnetics input view from a minimized or maximized
state.
•coresize(width,height) resizes theactivemagnetics inputwindowclient area to wid th
×height.
3.10.5 Miscellaneous
•coclose() closethecurrent postprocessorwindow.
•corefreshview() Redraws thecurrent view.
•coreload() Reloads thesolutionfrom disk.
•cosavebitmap("filename") saves a bitmapped screen shot of the current view to the
ﬁle speciﬁed by "filename" . Note that if you use a path you must use two backslashes
(e.g."c:\\temp\\myfile.bmp" ). If the ﬁle name contains a space (e.g. ﬁle names like
c:\program ﬁles \stuff) you must enclose the ﬁle name in (extra) quotes by usin g a\"se-
quence. Forexample:
cosavebitmap(" \"c:\\temp\\screenshot.bmp \"")
•cosavemetafile("filename") saves a metaﬁle screenshot of the current view to the ﬁle
speciﬁed by "filename" , subject to the printf-type formatting explained previous ly for the
savebitmap command.
•coshownames(flag) Thisfunction allowtheuserto displayor hidetheblocklabe l names
on screen. To hide the block label names, flagshould be 0. To display the names, the
parametershouldbesetto 1.
•conumnodes() Returns thenumberofnodesin thein focus current ﬂowoutput mesh.
•conumelements() Returns the number of elements in the in focus current ﬂow out put
mesh.
•cogetnode(n) Returns the(x,y)or(r,z)positionofthenthmeshnode.
•cogetelement(n) MOGetElement[n]returnsthefollowingproprertiesforthe nthelement:
1. Index ofﬁrst elementnode
2. Index ofsecondelement node
3. Index ofthirdelementnode
139

---

4. x (orr) coordinateoftheelement centroid
5. y (orz) coordinateoftheelementcentroid
6. element area usingthelengthunitdeﬁned fortheproblem
7. group numberassociatedwiththeelement
140