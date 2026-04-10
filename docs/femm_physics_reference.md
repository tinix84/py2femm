# FEMM 4.2 Physics and Material Properties Reference

> Extracted from the FEMM 4.2 User Manual (October 25, 2015)

Chapter1
Introduction
FEMMisasuiteofprogramsforsolvinglowfrequencyelectro magneticproblemsontwo-dimensional
planar and axisymmetric domains. The program currently add resses linear/nonlinear magneto-
static problems, linear/nonlinear time harmonic magnetic problems, linear electrostatic problems,
and steady-stateheat ﬂowproblems.
FEMM isdividedintothreeparts:
•Interactiveshell ( femm.exe ). This program is a MultipleDocument Interface pre-proces sor
andapost-processorforthevarioustypesofproblemssolve dbyFEMM.ItcontainsaCAD-
like interface for laying out the geometry of the problem to b e solved and for deﬁning ma-
terial properties and boundary conditions. Autocad DXF ﬁle s can be imported to facilitate
the analysis of existing geometries. Field solutions can be displayed in the form of contour
anddensityplots. Theprogramalsoallowstheusertoinspec ttheﬁeldatarbitrarypoints,as
well as evaluate a number of different integrals and plot var ious quantities of interest along
user-deﬁned contours.
•triangle.exe . Triangle breaks down the solution region into a large numbe r of triangles,
a vital part of the ﬁnite element process. This program was wr itten by JonathanShewchuk
and isavailableat www.cs.cmu.edu/quake/triangle.html
•Solvers ( fkern.exe for magnetics; belasolv for electrostatics); hsolvfor heat ﬂow prob-
lems;and csolvforcurrentﬂowproblems.. Eachsolvertakesasetofdataﬁle sthatdescribe
problemandsolvestherelevantpartialdifferentialequat ionstoobtainvaluesforthedesired
ﬁeld throughoutthesolutiondomain.
The Lua scriptinglanguageis integrated into theinteracti veshell. Unlikeprevious versionsof
FEMM (i.e.v3.4 and lower), only one instance of Lua is running at any one time. This single
instance of Lua can both build and analyze a geometry and eval uate the post-processing results,
simplifyingthecreation ofvarioussorts of“batch” runs.
Inaddition,alleditboxesintheuserinterfaceareparsedb yLua,allowingequationsormathe-
matical expressionsto be entered into any edit boxin lieu of anumerical value. In any edit boxin
FEMM, a selected piece of text can be evaluated by Lua via a sel ection on the right mousebutton
menu.
The purpose of this document is to give a brief explanation of the kind of problems solved by
FEMMand toprovideafairly detaileddocumentationofthepr ograms’use.
6

---

1.1 Overview
The goal of this section is to give the user a brief descriptio n of the problems that FEMM solves.
This information is not really crucial if you are not particu larly interested in the approach that
FEMM takes to formulating the problems. You can skip most of Overview , but take a look at
Section 1.3. This section contains some important pointers about assigning enough boundary
conditionstoget asolvableproblem.
SomefamiliaritywithelectromagnetismandMaxwell’sequa tionsisassumed,sinceareviewof
thismaterialisbeyondthescopeofthismanual. However,th eauthorhasfoundseveralreferences
that have proved useful in understanding the derivation and solution of Maxwell’s equations in
various situations. A very good introductory-level text fo r magnetic and electrostatic problems is
Plonus’sApplied electromagnetics [1]. A good intermediate-levelreview of Maxwell’sequatio ns,
as well as a useful analogy of magnetism to similar problems i n other disciplines is contained
in Hoole’s Computer-aided analysis and design of electromagnetic dev ices[2]. For an advanced
treatment, the reader has no recourse but to refer to Jackson ’sClassical electrodynamics [3]. For
thermal problems, the author has found White’s Heat and mass tranfer [4] and Haberman’s Ele-
mentary applied partialdifferential equations [5] to be useful in understanding the derivationand
solutionofsteady-statetemperatureproblems.
1.2 RelevantPartialDifferentialEquations
FEMMaddressessomelimitingcasesofMaxwell’sequations. Themagneticsproblemsaddressed
arethosethatcan beconsidedas “lowfrequencyproblems,”i nwhich displacmentcurrents can be
ignored. Displacementcurrentsaretypicallyrelevanttom agneticsproblemsonlyatradiofrequen-
cies. In asimilarvein,theelectrostaticssolverconsider stheconversecase inwhich onlytheelec-
tric ﬁeld is considered and the magnetic ﬁeld is neglected. F EMM also solves 2D/axysymmetric
steady-stateheatconductionproblems. Thisheatconducti onproblemismathematicallyverysim-
ilartothesolutionofelectrostaticproblems.
1.2.1 MagnetostaticProblems
Magnetostatic problems are problems in which the ﬁelds are t ime-invariant. In this case, the ﬁeld
intensity(H)andﬂuxdensity (B) mustobey:
∇×H=J (1.1)
∇·B=0 (1.2)
subjectto aconstitutiverelationshipbetween BandHforeach material:
B=µH (1.3)
If a material is nonlinear ( e.g.saturating iron or alnico magnets), the permeability, µis actually a
functionof B:
µ=B
H(B)(1.4)
7

---

FEMM goes about ﬁnding a ﬁeld that satisﬁes (1.1)-(1.3) via a magnetic vector potential ap-
proach. Fluxdensityis writtenintermsofthevectorpotent ial,A, as:
B=∇×A (1.5)
Now,thisdeﬁnitionof Balways satisﬁes(1.2). Then,(1.1)can berewrittenas:
∇×/parenleftbigg1
µ(B)∇×A/parenrightbigg
=J (1.6)
Foralinearisotropicmaterial (and assumingtheCoulombga uge,∇·A=0), eq. (1.6)reduces to:
−1
µ∇2A=J (1.7)
FEMMretainstheformof(1.6),sothatmagnetostaticproble mswithanonlinear B-Hrelationship
can besolved.
In the general 3-D case, Ais a vector with three components. However, in the 2-D planar and
axisymmetriccases,twoofthesethreecomponentsarezero, leavingjustthecomponentinthe“out
ofthepage”direction.
The advantage of using the vector potential formulation is t hat all the conditions to be satis-
ﬁed have been combined into a single equation. If Ais found, BandHcan then be deduced by
differentiating A. The form of (1.6), an elliptic partial differential equati on, arises in the study of
manydifferenttypesofengineeringphenomenon. Therearea largenumberoftoolsthathavebeen
developedovertheyears to solvethisparticularproblem.
1.2.2 Time-HarmonicMagnetic Problems
If the magnetic ﬁeld is time-varying, eddy currents can be in duced in materials with a non-zero
conductivity. Several other Maxwell’s equations related t o the electric ﬁeld distributionmust also
be accommodated. Denoting the electric ﬁeld intensity asEand thecurrent density asJ,EandJ
obeytheconstitutiverelationship:
J=σE (1.8)
Theinducedelectricﬁeld then obeys:
∇×E=−∂B
∂t(1.9)
Substitutingthevectorpotentialform ofBinto(1.9)yield s:
∇×E=−∇×˙A (1.10)
In thecaseof2-D problems,(1.10)can beintegratedtoyield :
E=−˙A−∇V (1.11)
and theconstitutiverelationship,(1.8)employedto yield :
J=−σ˙A−σ∇V (1.12)
8

---

Substitutinginto(1.6)yieldsthepartialdifferentialeq uation:
∇×/parenleftbigg1
µ(B)∇×A/parenrightbigg
=−σ˙A+Jsrc−σ∇V (1.13)
whereJsrcrepresents the applied currents sources. The ∇Vterm is an additional voltage gradient
that, in 2-D problems, is constant over a conducting body. FE MM uses this voltage gradient in
someharmonicproblemsto enforceconstraintsonthecurren t carried by conductiveregions.
FEMMconsiders(1.13)forthecaseinwhichtheﬁeldisoscill atingatoneﬁxedfrequency. For
thiscase,a phasortransformation [2]yieldsasteady-stateequationthatissolvedfortheamp litude
and phaseof A. Thistransformationis:
A=Re[a(cosωt+jsinωt)=]=Re/bracketleftbig
aejwt/bracketrightbig
(1.14)
inwhichaisacomplexnumber. Substitutinginto(1.13)anddividingo utthecomplexexponential
term yieldstheequationthatFEMM actuallysolvesforharmo nicmagneticproblems:
∇×/parenleftbigg1
µef f(B)∇×a/parenrightbigg
=−jωσa+ˆJsrc−σ∇V (1.15)
inwhich ˆJsrcrepresents thephasortransformoftheappliedcurrent sour ces.
Strictly speaking, the permeability µshould be constant for harmonic problems. However,
FEMM retains a nonlinear relationship in the harmonic formu lation, allowing the program to ap-
proximate the effects of saturation on the phase and amplitu de of the fundamental of the ﬁeld
distribution. The form of the BH curve is not exactly the same as in the DC case. Instead, “effec-
tivepermeability” µef fis selected to give the correct amplitude of the fundamental component of
the waveform under sinusoidal excitation. There are a numbe r of subtleties to the nonlinear time
harmonicformulation–thisformulationisaddressed inmor edetailinAppendixA.4.
FEMMalsoallowsfortheinclusionofcomplexandfrequency- dependentpermeabilityintime
harmonic problems. These features allow the program to mode l materials with thin laminations
and approximatelymodelhysteresiseffects.
1.2.3 ElectrostaticProblems
Electrostaticproblems considerthe behaviorof electric ﬁ eld intensity, E, and electric ﬂux density
(alternatively electric displacement), D. There are two conditions that these quantities must obey.
TheﬁrstconditionisthedifferentialformofGauss’Law,wh ichsaysthattheﬂuxoutofanyclosed
volumeisequal tothecharge containedwithinthevolume:
∇·D=ρ (1.16)
whereρrepresents chargedensity. Thesecond isthedifferentialf ormofAmpere’s looplaw:
∇×E=0 (1.17)
Displacementand ﬁeld intensityarealso related tooneanot herviatheconstitutiverelationship:
D=εE (1.18)
9

---

whereεistheelectricalpermittivity. Althoughsomeelectrostat icsproblemsmighthaveanonlinear
constitutiverelationshipbetween DandE, theprogram onlyconsiderslinearproblems.
To simplifythecomputationofﬁelds which satisfy thesecon ditions,the program employsthe
electricscalarpotential, V, deﬁned by itsrelationto Eas:
E=−∇V (1.19)
Becauseofthevectoridentity ∇×∇ψ=0foranyscalar ψ,Ampere’slooplawisautomatically
satisﬁed. SubstitutingintoGauss’Lawandapplyingthecon stitutiverelationshipyieldsthesecond-
orderpartial differentialequation:
−ε∇2V=ρ (1.20)
which applies over regions of homogeneous ε. The program solves (1.20) for voltage Vover a
user-deﬁned domainwithuser-deﬁned sourcesand boundaryc onditions.
1.2.4 HeatFlowProblems
The heat ﬂow problems address by FEMM are essentially steady -state heat conduction problems.
These probelms are represented by a temperature gradient, G(analogous to the ﬁeld intensity, E
for electrostaticproblems),and heat ﬂux density, F(analogousto electric ﬂux density, D, forelec-
trostaticproblems).
The heat ﬂux density must obey Gauss’ Law, which says that the heat ﬂux out of any closed
volumeis equal to theheat generation withinthe volume. Ana logousto the electrostaticproblem,
thislawisrepresented indifferentialform as:
∇·F=q (1.21)
whereqrepresents volumeheatgeneration.
Temperature gradient and heat ﬂux density are also related t o one another via the constitutive
relationship:
F=kG (1.22)
wherekisthethermalconductivity. Thermalconductivityisoften aweakfunctionoftemperature.
FEMMallowsforthevariationofconductivityasan arbitrar y functionoftemperature.
Ultimately, one is generally interested in discerning the t emperature, T, rather than the heat
ﬂux densityortemperaturegradient. Temperatureis relate d tothetemperaturegradient, G, by:
G=−∇T (1.23)
Substituting(1.23)intoGauss’Lawandapplyingtheconsti tutiverelationshipyieldsthesecond-
orderpartial differentialequation:
−∇·(k∇T)=q (1.24)
FEMMsolves(1.24)fortemperature Toverauser-deﬁned domainwithuser-deﬁned heatsources
and boundaryconditions.
10

---

1.2.5 Current FlowProblems
Thecurrent ﬂow problems solvedby FEMM are essentially quas i-electrostaticproblemsin which
the magnetic ﬁeld terms in Maxwell’s equations can be neglec ted but in which the displacement
current terms(neglected inmagnetostaticand eddy current problems)arerelevant.
AgainrestatingMaxwell’sEquations,theelectricand magn eticﬁelds mustobey:
∇×H=J+˙D (1.25)
∇·B=0 (1.26)
∇×E=−˙B (1.27)
∇·D=ρ (1.28)
subjectto theconstitutiverelations:
J=σE (1.29)
D=εE (1.30)
Thedivergenceof(1.25)can betaken toyield:
∇·(∇×H)=∇·J+∇·˙D (1.31)
By applicationofastandardvectoridentity,theleft-hand sideof(1.31) iszero, leadingto:
∇·J+∇·˙D=0 (1.32)
As before, wecan assumean electricpotential, V, that isrelated toﬁeld intensity, E, by:
E=−∇V (1.33)
Because theﬂux density, B, is assumedto benegligiblysmall,(1.26) and(1.27)are sui tablysatis-
ﬁed by thischoiceofpotential.
If a phasor transformation is again assumed, wherein differ entiation with respect to time is
replaced by multiplicationby jω, thedeﬁnitionofvoltagecan besubstitutedinto(1.32)toy ield:
−∇·((σ+jωε)∇V)=0 (1.34)
If it is assumed that the material properties are piece-wise continuous, things can be simpliﬁed
slightlyto:
−(σ+jωε)∇2V=0 (1.35)
FEMMsolves(1.35)to analyzecurrent ﬂow problems.
Eq. (1.35) also applies for the solution of DC current ﬂow pro blems. At zero frequency, the
term associatedwithelectrical permittivityvanishes,le aving:
−σ∇2V=0 (1.36)
By simplyspeciﬁng a zero frequency, this formulationsolve s DC current ﬂow problems in a con-
sistentfashion.
11

---

1.3 BoundaryConditions
Some discussion of boundary conditions is necessary so that the user will be sure to deﬁne an
adequatenumberofboundaryconditionsto guaranteeauniqu esolution.
1.3.1 Magnetic andElectrostaticBCs
Boundary conditionsformagneticand electrostaticproble mscomeinﬁvevarieties:
•Dirichlet. In this type of boundary condition, the value of potential AorVis explicitly
deﬁned on the boundary, e.g. A=0. The most common use of Dirichlet-type boundary
conditions in magnetic problems is to deﬁne A=0 along a boundary to keep magnetic ﬂux
from crossing the boundary. In electrostatic problems, Dir ichlet conditions are used to ﬁx
thevoltageofasurfacein theproblemdomain.
•Neumann . This boundary condition speciﬁes the normal derivative of potential along the
boundary. Inmagneticproblems,thehomogeneousNeumannbo undarycondition, ∂A/∂n=
0isdeﬁnedalongaboundarytoforceﬂuxtopasstheboundarya texactlya90oangletothe
boundary. This sort ofboundary conditionis consistentwit han interface with avery highly
permeablemetal.
•Robin. The Robin boundary condition is sort of a mix between Dirich let and Neumann,
prescribing a relationship between the value of Aand its normal derivativeat the boundary.
An exampleofthisboundaryconditionis:
∂A
∂n+cA=0
ThisboundaryconditionismostofteninFEMMtodeﬁne“imped anceboundaryconditions”
that allow a bounded domain to mimicthe behavior of an unboun ded region. In the context
of heat ﬂow problems, this boundary condition can be interpr eted as a convection boundary
condition. In heat ﬂow problems, radiation boundary condit ions are linearized about the
solution from the last iteration. The linearized form of the radiation boundary condition is
alsoaRobin boundarycondition.
•Periodic A periodic boundary conditions joins two boundaries togeth er. In this type of
boundary condition, the boundary values on corresponding p oints of the two boundaries
areset equal tooneanother.
•Antiperiodic Theantiperiodicboundaryconditionalsojoinstogethertw oboundaries. How-
ever,theboundaryvaluesare madeto beofequal magnitudebu toppositesign.
If no boundary conditions are explicitly deﬁned, each bound ary defaults to a homogeneous
Neumann boundary condition. However, a non-derivative bou ndary condition must be deﬁned
somewhere (or the potential must be deﬁned at one reference p oint in the domain) so that the
problemhas auniquesolution.
For axisymmetricmagneticproblems, A=0 is enforced on the line r=0. In thiscase, a valid
solutioncanbeobtainedwithoutexplicitlydeﬁninganybou ndaryconditions,aslongaspartofthe
boundaryoftheproblemliesalong r=0. Thisisnotthecase forelectrostaticproblems,however.
Forelectrostaticproblems,itisvalidtohaveasolutionwi thanon-zero potentialalong r=0.
12

---

1.3.2 HeatFlowBCs
Thereare sixtypesofboundaryconditionsforheat ﬂow probl ems:
•FixedTemperature Thetemperaturealongtheboundaryisset toa prescribedval ue.
•HeatFlux Theheatﬂux, f,acrossaboundaryisprescribed. Thisboundaryconditionc anbe
represented mathematicallyas:
k∂T
∂n+f=0 (1.37)
wherenrepresents thedirectionnormal totheboundary.
•Convection Convection occurs if the boundary is cooled by a ﬂuid ﬂow. Thi s boundary
conditioncan berepresented as:
k∂T
∂n+h(T−To)=0 (1.38)
wherehisthe“heat transfercoefﬁcient”and Tois theambientcoolingﬂuid temperature.
•Radiation Heat ﬂux viaradiationcan bedescribedmathematicallyas:
k∂T
∂n+βksb/parenleftbig
T4−T4
o/parenrightbig
=0 (1.39)
wherebetais the emissivityof the surface (a dimensionlessvalue betw een 0 and 1) and ksb
istheStefan-Boltzmann constant.
•Periodic A periodic boundary conditions joins two boundaries togeth er. In this type of
boundary condition, the boundary values on corresponding p oints of the two boundaries
areset equal tooneanother.
•Antiperiodic Theantiperiodicboundaryconditionalsojoinstogethertw oboundaries. How-
ever,theboundaryvaluesare madeto beofequal magnitudebu toppositesign.
Ifnoboundaryconditionsareexplicitlydeﬁned,eachbound arydefaultsaninsulatedcondition
(i.e.no heat ﬂux across the boundary). However, a non-derivative boundary condition must be
deﬁned somewhere (or the potential must be deﬁned at one refe rence point in the domain)so that
theproblemhasauniquesolution.
1.4 FiniteElementAnalysis
Although the differential equations of interest appear rel atively compact, it is typically very difﬁ-
cult to get closed-form solutions for all but the simplest ge ometries. This is where ﬁnite element
analysis comes in. The idea of ﬁnite elements is to break the p roblem down into a large number
regions,each witha simplegeometry ( e.g.triangles). Forexample,Figure1.1 showsa mapofthe
Massachusetts broken down into triangles. Over these simpl e regions, the “true” solution for the
13

---

Figure1.1: TriangulationofMassachusetts
desired potentialis approximated by avery simplefunction . If enoughsmall regionsare used, the
approximatepotentialcloselymatchestheexactsolution.
The advantage of breaking the domain down into a numberof sma ll elements is that the prob-
lem becomes transformed from a small butdifﬁcult to solvepr oblem into abig but relativelyeasy
to solve problem. Through the process of discretizaton, a li near algebra problem is formed with
perhaps tens of thousands of unknowns. However, algorithms exist that allow the resulting linear
algebraproblemtobesolved,usuallyinashortamountoftim e.
Speciﬁcally, FEMM discretizes the problem domain using tri angular elements. Over each
element, the solution is approximated by a linear interpola tion of the values of potential at the
three vertices of the triangle. The linear algebra problem i s formed by minimizing a measure
of the error between the exact differential equation and the approximate differential equation as
writtenin termsofthelineartrial functions.
14

---

2.2.6 Problem Deﬁnition
The deﬁnition of problem type is speciﬁed by choosing the Problem selection off of the main
menu. Selecting thisoptionbringsup theProblem Deﬁnition dialog,shownin Figure2.5
Figure2.5: Problem Deﬁnitiondialog.
Theﬁrstselectionisthe Problem Type droplist. Thisdropboxallowstheusertochoosefrom
a 2-D planar problem (the Planarselection), or an axisymmetric problem (the Axisymmetric
selection).
Nextisthe Length Units droplist. Thisboxidentiﬁeswhatunitisassociatedwithth edimen-
sions prescribed in the model’s geometry. Currently, the pr ogram supports inches, millimeters,
centimeters,meters,mils,and µmeters.
The ﬁrst edit box in the dialog is Frequency (Hz) . For a magnetostatic problem, the user
should choose a frequency of zero. If the frequency is non-ze ro, the program will perform a
harmonic analysis, in which all ﬁeld quantities are oscilla ting at this prescribed frequency. The
default frequencyis zero.
The second edit box is the Depthspeciﬁcation. If a Planar problem is selected, this edit box
becomes enabled. This value is the length of the geometry in t he “into the page” direction. This
value is used for scaling integral results in the post proces sor (e.g.force, inductance, etc.) to the
appropriate length. The units of the Depth selection are the same as the selected length units. For
ﬁles imported from version 3.2, the Depth is chosen so that th e depth equals 1 meter, since in
version3.2,all resultsfromplanarproblemsarereported p ermeter.
21

---

The third edit box is the Solver Precision edit box. The number in this edit box speciﬁes
thestoppingcriteriaforthelinearsolver. Thelinearalge braproblemcouldberepresented by:
Mx=b
whereMis a square matrix, bis a vector, and xis a vector of unknowns to be determined. The
solver precision value determines the maximum allowable va lue for||b−Mx||/||b||. The default
valueis 10−8.
The fourth edit box is labeled Min Angle . The entry in this box is used as a constraint in
the Triangle meshing program. Triangle adds points to the me sh to ensure that no angles smaller
than the speciﬁed angle occur. If the minimum angle is 20.7 de grees or smaller, the triangulation
algorithmistheoreticallyguaranteedtoterminate(assum inginﬁniteprecisionarithmetic–Triangle
may fail to terminate if you run out of precision). In practic e, the algorithm often succeeds for
minimum angles up to 33.8 degrees. For highly reﬁned meshes, however, it may be necessary
to reduce the minimum angle to well below 20 to avoid problems associated with insufﬁcient
ﬂoating-pointprecision. Theedit boxwillaccept valuesbe tween 1 and33.8 degrees.
Lastly,thereisanoptional Comment editbox. Theusercanenterinafewlinesoftextthatgive
a brief description of the problem that is being solved. This is useful if theuser is running several
small variations on a given geometry. The comment can then be used to identify the relevant
features foraparticulargeometry.
2.2.7 Deﬁnition of Properties
Tomakeasolvableproblemdeﬁnition,theusermustidentify boundaryconditions,blockmaterials
properties,andsoon. Thedifferenttypesofpropertiesdeﬁ ned foragivenproblemaredeﬁnedvia
theProperties selectionoffofthemainmenu.
When the Properties selection is chosen, a drop menu appears that has selections for Ma-
terials, Boundary, Point, and Circuits. When any one of thes e selections is chosen, the dialog
pictured in Figure 2.6 appears. This dialog is the manager fo r a particular type of properties. All
Figure2.6: Property Deﬁnitiondialogbox
currently deﬁned properties are displayed in the Property Name drop list at the top of the dia-
log. At the beginning of a new model deﬁnition, the box will be blank, since no properties have
22

---

yet been deﬁned. Pushing the Add Property button allows the user to deﬁne a new property
type. The Delete Property buttonremovesthedeﬁnitionofthepropertycurrentlyinvi ewinthe
Property Name box. The Modify Property buttonallowstheusertoviewand edittheproperty
currentlyselectedinthe Property Name box. Speciﬁcsfordeﬁningthevariouspropertytypesare
addressed inthefollowingsubsections.
In general, a number of these edit boxes prompt the user for bo th real and imaginary compo-
nents for entered values. If the problem you are deﬁning is ma gnetostatic (zero frequency), enter
the desired value in the box for the real component, and leave a zero in the box for the imaginary
component. The reason that femm uses this formalism is to obt ain a relatively smooth transition
from static to time-harmonic problems. Consider the deﬁnit ion of the Phasor transformation in
Eq. 1.14. The phasor transformation assumes that all ﬁeld va lues oscillate in time at a frequence
ofω. Thephasortransformationtakesthecosinepartoftheﬁeld valueandrepresentsitasthereal
part of a complex number. The imaginary part represents the m agnitude of the sine component,
90ooutofphase. Notewhat happensas thefrequency goesto zero:
lim
ω→0(arecosωt−aimsinωt)=are (2.1)
Therefore,themagnetostatic( ω=0)valuesarejustdescribedbytherealpartthespeciﬁedcom plex
number.
PointProperties
If a new point property is added or an existing point property modiﬁed, the Nodal Property
dialogboxappears. Thisdialogbox ispicturedin Figure2.7
The ﬁrst selection is the Nameedit box. The default name is “New Point Property,” but this
nameshouldbechanged to somethingthatdescribes theprope rty thatyouare deﬁning.
Next are edit boxes for deﬁning the vectorpotential, A, at a givenpoint, or prescribing a point
current,J, at a given point. The two deﬁnitions are mutually exclusive . Therefore, if there is a
nonzero value the Jbox, the program assumes that a point current is being deﬁned . Otherwise, it
isassumedthat apointvectorpotentialisbeingdeﬁned.
There is an edit box for vector point vectorpotential, A. A can be deﬁned as a complex value,
if desired. The units of Aare Weber/Meter. Typically, Aneeds to be deﬁned as some particular
values (usually zero) at some point in the solution domain fo r problems with derivativeboundary
conditionson allsides. Thisis thetypicaluseofdeﬁningap ointvectorpotential.
Lastly,thereisaneditboxforthedeﬁnitionofapointcurre nt,J. Theunitsforthepointcurrent
are inAmperes. Thevalueof Jcan bedeﬁned as complex,ifdesired.
Boundary Properties
TheBoundary Property dialog box is used to specify the properties of line segments or arc
segments that are to be boundaries of the solution domain. Wh en a new boundary property is
added or an existing property modiﬁed, the Boundary Property dialog pictured in Figure 2.8
appears.
The ﬁrst selection in the dialog is the Nameof theproperty. The default name is “New Bound-
ary,”butyoushouldchangethisnametosomethingmoredescr iptiveoftheboundarythatisbeing
deﬁned.
23

---

Figure2.7: NodalProperty dialog.
The next selection is the BC Type drop list. This speciﬁes the boundary condition type. Cur-
rently,FEMMsupportsthefollowingtypesofboundaries:
•Prescribed A With this type of boundary condition, the vector potential, A, is prescribed
along a given boundary. This boundary condition can be used t o prescribe the ﬂux passing
normal to a boundary, since the normal ﬂux is equal to the tang ential derivative of Aalong
the boundary. The form for Aalong the boundary is speciﬁed via the parameters A0,A1,
A2andφin thePrescribed A parameters box. If the problem is planar, the parameters
correspondto theformula:
A=(A0+A1x+A2y)ejφ(2.2)
Iftheproblemtypeis axisymmetric,theparameters corresp ond to:
A=(A0+A1r+A2z)ejφ(2.3)
•Small Skin Depth This boundary condition denotes an interface with a materia l subject
to eddy currents at high enough frequencies such that the ski n depth in the material is very
small. Agooddiscussionofthederivationofthistypeofbou ndaryconditioniscontainedin
[2]. TheresultisaRobin boundaryconditionwithcomplexco efﬁcients oftheform:
∂A
∂n+/parenleftbigg1+j
δ/parenrightbigg
A=0 (2.4)
24

---

Figure2.8: Boundary Property dialog.
where the ndenotes the direction of the outward normal to the boundary a ndδdenotes the
skindepthofthematerialat thefrequencyofinterest. Thes kindepth, δis deﬁned as:
δ=/radicalBigg
2
ωµrµoσ(2.5)
whereµrandσaretherelativepermeabilityandconductivityofthethins kindeptheddycur-
rentmaterial. Theseparametersaredeﬁnedbyspecifying µandσintheSmall skin depth
parameters box in the dialog. At zero frequency, this boundary conditio n degenerates to
∂A/∂n=0 (because skindepthgoesto inﬁnity).
•MixedThisdenotesaboundaryconditionoftheform:
/parenleftbigg1
µrµo/parenrightbigg∂A
∂n+coA+c1=0 (2.6)
Theparametersforthisclassofboundaryconditionarespec iﬁedinthe Mixed BC parameters
boxinthedialog. Bythechoiceofcoefﬁcients,thisboundar yconditioncaneitherbeaRobin
oraNeumannboundarycondition. Therearetwo mainusesofth isboundarycondition:
1. By carefully selecting the c0coefﬁcient and specifying c1=0, this boundary condi-
tion can be applied to the outer boundary of your geometry to a pproximate an up-
bounded solution region. For more information on open bound ary problems, refer to
AppendixA.3.
25

---

2. TheMixedboundaryconditioncanusedtosettheﬁeld inten sity,H,thatﬂowsparallel
to a boundary. This is done by setting c0to zero, and c1to the desired value of Hin
units of Amp/Meter. Note that this boundary condition can al so be used to prescribe
∂A/∂n=0 at the boundary. However, this is unnecessary–the 1storder triangle ﬁnite
elements givea ∂A/∂n=0 boundaryconditionby default.
•Strategic Dual Image This is sort of an “experimental” boundary condition that I h ave
found useful for my own purposes from time to time. This bound ary condition mimics
an “open” boundary by solving the problem twice: once with a h omogeneous Dirichlet
boundaryconditionontheSDIboundary,andoncewithahomog eneousNeumanncondition
on theSDI boundary. Theresults from each run are then averag ed to get the open boundary
result. This boundary condition should only be applied to th e outer boundary of a circular
domain in 2-D planar problems. Through a method-of-images a rgument, it can be shown
thatthisapproachyieldsthecorrect open-boundaryresult forproblemswithnoiron( i.ejust
currents orlinearmagnetswithunitpermeabilityinthesol utionregion).
•Periodic This type of boundary condition is applied to either two segm ents or two arcs to
force themagneticvectorpotentialto beidentical along ea ch boundary. Thissort of bound-
ary is useful in exploiting the symmetry inherent in some pro blems to reduce the size of
thedomainwhichmustbemodeled. Thedomainmerelyneedstob eperiodic,asopposedto
obeyingmorerestrictive A=0or∂A/∂n=0lineofsymmetryconditions. Anotherusefulap-
plicationofperiodicboundaryconditionsisforthemodeli ngof“openboundary”problems,
as discussed in Appendix A.3.3. Often, a periodic boundary i s made up of several different
line or arc segments. A different periodic condition must be deﬁned for each section of the
boundary, since each periodic BC can only be applied to a line or arc and a corresponding
lineorarc ontheremoteperiodicboundary.
•Antiperiodic The antiperiodicboundary condition is applied in a similar way as the peri-
odic boundary condition, but its effect is to force two bound aries to be the negative of one
another. This type of boundary is also typically used to redu ce the domain which must be
modeled, e.g.so that an electric machine might be modeled for the purposes of a ﬁnite
elementanalysiswithjustonepole.
MaterialsProperties
TheBlock Property dialog box is used to specify the properties to be associated with block la-
bels. Thepropertiesspeciﬁedinthisdialoghavetodowitht hematerialthattheblockiscomposed
of, as well as some attributes about how the material is put to gether (laminated). When a new
material property is added or an existingproperty modiﬁed, theBlock Property dialog pictured
inFigure2.9 appears.
As with Point and Boundary properties, the ﬁrst step is to cho ose a descriptive name for the
materialthat isbeingdescribed. Enteritinthe Nameeditbox inlieu of“New Material.”
Next decide whether the material will have a linear or nonlin ear B-H curve by selecting the
appropriateentryin the B-H Curve drop list.
IfLinear B-H Relationship was selected from the drop list, the next group of Linear
Material Properties parameters will become enabled. FEMM allows you to specify d ifferent
26

---

Figure 2.9: Block Property dialog.
27

---

relativepermeabilitiesintheverticalandhorizontaldir ections(µxforthex-orhorizontaldirection,
andµyforthey-orvertical direction).
There are also boxes for φhxandφhy, which denote the hysteresis lag angle corresponding to
each direction, to be used in cases in which linear material p roperties have been speciﬁed. A
simple, but surprisingly effective, model for hysteresis i n harmonic problems is to assume that
hysteresis creates a constant phase lag between B and H that i s independent of frequency. This is
exactlythesameasassumingthathysteresisloophasan elli pticalshape. Sincethehysteresisloop
isnotexactlyelliptical,theperceivedhysteresisanglew illvarysomewhatfordifferentamplitudes
of excitation. The hysteresis angle is typically not a param eter that appears on manufacturer’s
data sheets; you have to identify it yourself from a frequenc y sweep on a toroidal coil with a core
composedofthematerialofinterest. Formostlaminatedste els,thehysteresisangleliesbetween0o
and 20o[6]. Thissamereference alsohas averygooddiscussionofth ederivationandapplication
oftheﬁxedphaselag modelofhysteresis.
IfNonlinear B-H Curve wasselectedfromthedroplist,the Nonlinear Material Properties
parametergroupbecomesenabled. ToenterinpointsonyourB -Hcurve,hitthe Edit B-H Curve
button. When the button is pushed a dialog appears that allow s you to enter in B-H data (see Fig-
ure2.10. Theinformationtobeenteredinthesedialogsisus uallyobtainedbypickingpointsoffof
Figure2.10: B-H dataentrydialog.
manufacturer’s data sheets. For obviousreasons, you muste nter the same numberof pointsin the
28

---

“B” (ﬂux density) column as in the “H” (ﬁeld intensity) colum n. To deﬁne a nonlinear material,
youmustenter atleastthreepoints,and youshouldentertenorﬁfteen toget agoodﬁ t.
Afteryou aredoneentering inyourB-H datapoints,itisagoo dideatoviewtheB-H curveto
see that it looks like it is “supposed” to. This is done by pres sing the Plot B-H Curve button or
theLog Plot B-H Curve button on the B-H data dialog. You should see a B-H curve that l ooks
something like the curve pictured in Figure 2.11. The boxes i n the plot represent the locations of
Figure2.11: SampleB-H curveplot.
theentered B-H points,and thelinerepresents acubicsplin ederivedfrom theentered data. Since
FEMM interpolates between your B-H points using cubic splin es, it is possibleto get a bad curve
if you haven’t entered an adequate number of points. “Weird” B-H curves can result if you have
entered too few points around relatively sudden changes in t he B-H curve. Femm “takes care of”
bad B-H data ( i.e.B-H data that would result in a cubic spline ﬁt that is not sing le-valued) by
repeatedly smoothingthe B-H data using a three-point movin gaverage ﬁlter until a ﬁt is obtained
that is single-valued. This approach is robust in the sense t hat it always yields a single-valued
curve, but the result might be a poor match to the original B-H data. Adding more data points in
thesectionsofthecurvewherethecurvatureis highhelpsto eliminatetheneed forsmoothing.
It may also be important to note that FEMM extrapolates linea rly off the end of your B-H
curve if the program encounters ﬂux density/ﬁeld intensity levels that are out of the range of the
valuesthatyouhaveentered. Thisextrapolationmaymaketh emateriallookmorepermeablethan
it “really” is at high ﬂux densities. You have to be careful to enter enough B-H values to get an
accurate solution in highly saturated structures so that th e program is interpolating between your
29

---

entered datapoints,rather thanextrapolating.
Also in the nonlinear parameters box is a parameter, φhmax. For nonlinear problems, the hys-
teresis lag is assumed to be proportional to the effective pe rmeability. At the highest effective
permeability,thehysteresisangleisassumedtoreachitsm aximalvalueof φhmax. Thisideacanbe
represented by theformula:
φh(B)=/parenleftbiggµef f(B)
µef f,max/parenrightbigg
φhmax (2.7)
The next entry in the dialog is Hc. If the material is a permanent magnet, you should enter
the magnet’s coercivity here in units of Amperes per meter. T here are some subtleties involved
in deﬁning permanent magnet properties (especially nonlin ear permanent magnets). Please refer
to the Appendix A.1 for a more thorough discussion of the mode ling of permanent magnets in
FEMM.
The next entry represents J, the source current density in the block. The ”source curren t den-
sity”denotesthecurrentintheblockatDC.Atfrequencieso therthanDCinaregionwithnon-zero
conductivity, eddy currents will be induced which will chan ge the total current density so that it
is no longer equal to the source current density. Use ”circui t properties” to imposea value for the
totalcurrentcarriedinaregionwitheddycurrents. Source currentdensitycanbecomplexvalued,
ifdesired.
Theσedit box denotes the electrical conductivity of the materia l in the block. This value is
generally only used in time-harmonic(eddy current) proble ms. The units for conductivityare 106
Seymens/Meter(equivalentto106(Ω∗Meters)−1). Forreference, copperatroom temperaturehas
aconductivityof58MS/m;agoodsiliconsteelformotorlami nationsmighthaveaconductivityof
as low as 2 MS/m. Commodity-gradetransformer laminationsa re more like9 MS/m. You should
notethat conductivitygenerally has a strong dependence up on temperature, so you shouldchoose
yourvaluesofconductivitykeepingthiscaveat inmind.
The last set of properties is the Lamination and Wire Type section. If the material is lami-
nated,thedroplistinthissectionisusedtodenotethedire ctioninwhichthematerialislaminated.
Ifthematerialismeanttorepresentabulkwoundcoil,thisd roplistspeciﬁesthesortofwirefrom
whichthecoilis constructed.
The various selections in this list are illustrated in Figur e 2.12 Currently, the laminations are
Figure2.12: Different laminationorientationoptions.
30

---

constrainedto runalong aparticularaxis.
If some sort of laminated construction is selected in the dro p list, the lamination thickness
and ﬁll factor edit boxes become enabled. The lamination thi ckness, ﬁll factor, and lamination
orientation parameters are used to implement a bulk model of laminated material. The result of
this model is that one can account for laminations with hyste resis and eddy currents in harmonic
problems. For magnetostatic problems, one can approximate the effects of nonlinear laminations
without the necessity of modeling the individual laminatio ns separately. This bulk lamination
modelisdiscussedin moredetailin theAppendix(Section A. 2).
Thedlamedit box represents the thickness of the laminations used fo r this type of material. If
thematerialisnotlaminated,enter0inthiseditbox. Other wise,enterthethicknessof justtheiron
part(nottheironplustheinsulation)in thisedit boxin unitsof millimeters.
Associated with the lamination thickness edit box is the Lam fill factor edit box. This is
the fraction of the core that is ﬁlled with iron. For example, if you had a lamination in which the
iron was 12.8 mils thick, and the insulationbewteen laminat ions was 1.2 mils thick, the ﬁll factor
wouldbe:
FillFactor =12.8
1.2+12.8=0.914
If a wire type is selected, the Strand dia. and/or Number of strands edit boxes become
enabled. Ifthe Magnet wire orSquare wire typesareselected, it isunderstoodthatthereis can
only be one strand, and the Number of strands edit box is disabled. The wire’s diameter (or
width) is then entered in the Strand dia. edit box. For stranded and Litz wire, one enters the
number of strands and the strand diameter. Currently, only b uilds with a single strand gauge are
supported.
If a wire type is speciﬁed, the material property can be appli ed to a “bulk” coil region each
individual turn need not be modeled. In DC problems, the resu lts will automatically be adjusted
for the implied ﬁll factor. For AC problems, the the ﬁll facto r is taken into account, and AC
proximity and skin effect losses are taken into account via e ffective complex permeability and
conductivitythatareautomaticallycomputedforthewound region.
MaterialsLibrary
Since one kind of material might be needed in several differe nt models, FEMM has a built-in li-
brary of Block Property deﬁnitions. The user can access and m aintain this library through the
Properties | Materials Library selection off of the main menu. When this option is se-
lected,the Materials Library dialogpicturedinFigure2.13appears. Thisdialogallowth euser
to exchange Block Property deﬁnitions between the current m odel and the materials library via a
drag-and-drop interface.
A number of different options are available via a mouse butto n right-click when the cursor is
located on top of a material or folder. Materials can be edite d by double-clicking on the desired
material.
Material from other material libraries or models can be impo rted by selecting the “Import
Materials” option from the right-button menu that appears w hen the pointer is over the root-level
folderofeithertheLibrary orModelmaterialslists.
The materials library should be located in the same director y as the FEMM executable ﬁles,
undertheﬁlename mlibrary.dat . Ifyoumovethematerialslibrary,femmwillnotbeabletoﬁn d
31

---

Figure2.13: MaterialsLibrarydialog.
it.
CircuitProperties
Thepurposeofthecircuitpropertiesistoallowtheusertoa pplyconstraintsonthecurrentﬂowing
inoneormoreblocks. Circuitscan bedeﬁned as either”paral lel”or”series”connected.
If”parallel”isselected,thecurrentissplitbetweenallr egionsmarkedwiththatcircuitproperty
onthebasisofimpedance(currentissplitsuchthatthevolt agedropisthesameacrossallsections
connected inparallel). Onlysolidconductorscan beconnec ted inparallel.
If ”series” is selected, the speciﬁed current is applied to e ach block labeled with that circuit
property. In addition, blocks that are labeled with a series circuit property can also be assigned a
numberofturns,suchthattheregionistreatedasastranded conductorinwhichthetotalcurrentis
theseries circuitcurrent timesthenumberofturnsin there gion. Thenumberofturnsfor aregion
isprescribedasablocklabelpropertyfortheregionofinte rest. Allstrandedcoilsmustbedeﬁned
as series-connected (because each turn is connected togeth er with the other turns in series). Note
thatthenumberofturnsassignedtoablocklabelcanbeeithe rapositiveoranegativenumber. The
signonthenumberofturnsindicatedthedirectionofcurren tﬂowassociatedwithapositive-valued
circuitcurrent.
For magnetostatic problems, one could alternatively apply a source current density over the
32

---

conductorofinterestandachievesimilarresults. Foreddy currentproblems,however,the“circuit”
properties are much more useful–they allow the user to deﬁne the current directly, and they allow
the userto assign a particular connectivityto various regi onsof the geometry. This information is
used toobtainimpedance,ﬂux linkage,etc., in arelatively painlessway inthepostprocessor.
By applying circuit properties, one can also enforce connec tivity in eddy current problems.
By default, all objects in eddy current problems are “shorte d together at inﬁnity”–that is, there
is nothing to stop induced currents from returning in other s ections of the domain that might not
be intended to be physically connected. By applying a parall el-connected circuit with a zero net
current density constraint to each physical “part” in the ge ometry, the connectivity of each part is
enforced and all isforced to beconservedinsidethepartofi nterest.
Thedialogforentering circuitpropertiesis picturedinFi gure 2.14.
Figure2.14: CircuitProperty dialog
2.2.8 ExteriorRegion
Oneoftendesirestosolveproblemsonanunboundeddomain. A ppendixA.3.3describesan easy-
to-implement conformal mapping method for representing an unbounded domain in a 2D planar
ﬁnite element analysis. Essentially, one models two disks– one represents the solution region of
interest and contains all of the items of interest, around wh ich one desires to determine the mag-
netic ﬁeld. The second disk represents the region exterior t o the ﬁrst disk. If periodic boundary
conditions are employed to link the edges of the two disks, it can be shown (see Appendix A.3.3)
thattheresultis exactlyequivalenttosolvingfor theﬁeld s inan unboundeddomain.
One would also liketo apply thesameapproach to model unboun dedaxisymmetricproblems,
as well as unbounded planar problems. Unfortunately, the Ke lvin Transformation is a bit more
complicated for axisymmetric problems. In this case, the pe rmeability of the external region has
tovarybasedondistancefromthecenteroftheexternalregi onandtheouterradiusoftheexternal
region. Theapproachisdescribedindetailin[20]. FEMMaut omaticallyimplementsthevariation
of permeability in the exterior region, but a bit more inform ation must be collected to perform
the permeability grading required in the external region. T his is where the “External Region”
parameters come in–these are the parameters that the progra m needs to deﬁne the permeabilities
ofelementsintheexternalregionfor“unbounded”axisymme tricproblems.
33

---

Speciﬁcally, there are three parametes that are collected i n the dialog that appears when the
userselectstheExternalRegion properties. Theseare:
•Center of Exterior Region The location along the z-axis of the axisymmetric problem
wherethecenteroftheblockrepresentingtheexternalregi onis located.
•Radius of Exterior Region Radius ofthesphererepresenting theexteriorregion.
•Radius of Interior Region Radious of the spehre representing the interior region ( i.e.
theregionin whichtheitemsofinterestarelocated).
To ﬁnish deﬁning the axisymmetric external region, the Block located in an external
regioncheckboxmustbeselectedinanyblocklabelsthatarelocate dintheregionthatisdesired
tobetheaxisymmetricexternal region.
2.2.9 AnalysisTasks
Meshingthemodel,analyzingthemodel,andviewingtheresu ltsaremosteasilyperformedbythe
toolbarbuttonspictured inFigure2.15
Figure2.15: Toolbarbuttonsforstartinganalysistasks.
The ﬁrst of these buttons (with the “yellow mesh” icon) runs t he mesh generator. The solver
actually automatically calls the mesh generator to make sur e that the mesh is up to date, so you
neverhaveto call the mesher from within femm. However, it is almost alw ays important to get
a look at the mesh and see that it “looks right.” When the mesh g eneration button is pressed,
the mesher is called. While the mesher is running, an entry la beled “triangle” will appear on
the Windows taskbar. After the geometry is triangulated, th e ﬁnite element mesh is loaded into
memoryanddisplayedunderneaththedeﬁnednodes,segments ,andblocklabelsasasetofyellow
lines.
If you have a very large model, just keeping all of the mesh inf ormation in core can take up
a signiﬁcant amount of memory. If you are about to analyze a ve ry large problem, it might be a
good idea to choose the Mesh | Purge Mesh option off of the main menu. When this option is
selected, the mesh is removed from memory, and the memory tha t it occupied is freed for other
uses.
The second button, with the “hand-crank” icon, executes the solver, fkern.exe . Before fkern
is actually run, the Triangle is called to make sure the mesh i s up to date. Then, fkern is called.
When fkern runs, it opens up a console window to display statu s information to the user. How-
ever, fkern requires no user interaction while it is running . When fkern is ﬁnished analyzing your
problem, the console window will disappear. The time that fk ern requires is highly dependent
on the problem being solved. Solution times can range from le ss than a second to several hours,
dependinguponthesizeandcomplexityoftheproblem. Gener ally,linearmagnetostaticproblems
take the least amount of time. Harmonic problems take slight ly more time, because the answer is
in terms of complex numbers. The complex numbers effectivel y double the number of unknowns
34

---

Figure2.24: Circuitresultsdialog.
2.4.1 Problem Deﬁnition
The deﬁnition of problem type is speciﬁed by choosing the Problem selection off of the main
menu. Selecting thisoptionbringsup theProblem Deﬁnition dialog,shownin Figure2.25.
Theﬁrstselectionisthe Problem Type droplist. Thisdropboxallowstheusertochoosefrom
a 2-D planar problem (the Planarselection), or an axisymmetric problem (the Axisymmetric
selection).
Nextisthe Length Units droplist. Thisboxidentiﬁeswhatunitisassociatedwithth edimen-
sions prescribed in the model’s geometry. Currently, the pr ogram supports inches, millimeters,
centimeters,meters,mils,and µmeters.
The ﬁrst edit box is the Depthspeciﬁcation. If a Planar problem is selected, this edit box
becomes enabled. This value is the length of the geometry in t he “into the page” direction. This
value is used for scaling integral results in the post proces sor (e.g. force, inductance, etc.) to the
appropriatelength. TheunitsoftheDepth selectionare the sameas theselected lengthunits.
Thesecondeditboxisthe Solver Precision editbox. Thenumberinthiseditboxspeciﬁes
thestoppingcriteriaforthelinearsolver. Thelinearalge braproblemcouldberepresented by:
Mx=b (2.17)
whereMis a square matrix, bis a vector, and xis a vector of unknowns to be determined. The
solver precision value determines the maximum allowable va lue for||b−Mx||/||b||. The default
valueis 10−8.
The third edit box is labeled Min Angle . The entry in this box is used as a constraint in the
Triangle meshing program. Triangle adds points to the mesh t o ensure that no angles smaller
47

---

Figure2.25: Problem Deﬁnitiondialog.
than the speciﬁed angle occur. If the minimum angle is 20.7 de grees or smaller, the triangulation
algorithmistheoreticallyguaranteedtoterminate(assum inginﬁniteprecisionarithmetic–Triangle
may fail to terminate if you run out of precision). In practic e, the algorithm often succeeds for
minimum angles up to 33.8 degrees. For highly reﬁned meshes, however, it may be necessary
to reduce the minimum angle to well below 20 to avoid problems associated with insufﬁcient
ﬂoating-pointprecision. Theedit boxwillaccept valuesbe tween 1 and33.8 degrees.
Lastly,thereisanoptional Comment editbox. Theusercanenterinafewlinesoftextthatgive
a brief description of the problem that is being solved. This is useful if theuser is running several
small variations on a given geometry. The comment can then be used to identify the relevant
features foraparticulargeometry.
2.4.2 Deﬁnition of Properties
Tomakeasolvableproblemdeﬁnition,theusermustidentify boundaryconditions,blockmaterials
properties,andsoon. Thedifferenttypesofpropertiesdeﬁ ned foragivenproblemaredeﬁnedvia
theProperties selectionoffofthemainmenu.
When the Properties selection is chosen, a drop menu appears that has selections for Ma-
terials, Boundary, Point, and Conductors. When any one of th ese selections is chosen, the dialog
picturedin Figure2.26appears.
This dialog is the manager for a particular type of propertie s. All currently deﬁned properties
are displayed in the Property Name drop list at the top of the dialog. At the beginning of a new
modeldeﬁnition,theboxwillbeblank,sincenopropertiesh aveyetbeendeﬁned. Pushingthe Add
48

---

Figure2.26: Property Deﬁnitiondialogbox.
Property button allows the user to deﬁne a new property type. The Delete Property button
removes the deﬁnition of the property currently in view in th eProperty Name box. The Modify
Property button allowsthe user to view and edit the property currentl y selected in the Property
Namebox. Speciﬁcs for deﬁning thevariousproperty types are add ressed in thefollowingsubsec-
tions.
PointProperties
If a new point property is added or an existing point property modiﬁed, the Nodal Property
dialogboxappears. Thisdialogbox ispicturedin Figure2.2 7.
Figure2.27: NodalProperty dialog.
The ﬁrst selection is the Nameedit box. The default name is “New Point Property,” but this
nameshouldbechanged to somethingthatdescribes theprope rty thatyouare deﬁning.
49

---

Next are edit boxes for deﬁning the voltage at a given point, o r prescribing a point charge
density at a given point. The type of point property is chosen via the radio buttons, and the value
isentered in theenablededit box.
Boundary Properties
TheBoundary Property dialog box is used to specify the properties of line segments or arc
segments that are to be boundaries of the solution domain. Wh en a new boundary property is
added or an existing property modiﬁed, the Boundary Property dialog pictured in Figure 2.28
appears.
Figure2.28: Boundary Property dialog.
The ﬁrst selection in the dialog is the Nameof theproperty. The default name is “New Bound-
ary,”butyoushouldchangethisnametosomethingmoredescr iptiveoftheboundarythatisbeing
deﬁned.
The next selection is the BC Type drop list. This speciﬁes the boundary condition type. Cur-
rently,FEMMelectrostaticsproblemssupportthefollowin gtypesofboundaries:
Fixed Voltage With this type of boundary condition, potential Vis set to a prescribed along
agivenboundary
MixedThisdenotes aboundaryconditionoftheform:
εrεo∂V
∂n+coV+c1=0 (2.18)
Theparametersforthisclassofboundaryconditionarespec iﬁedinthe Mixed BC parameters
box in the dialog. By the choice of coefﬁcients, this boundar y condition can either be a Robin or
a Neumann boundary condition. By carefully selecting the c0coefﬁcient and specifying c1=0,
this boundary condition can be applied to the outer boundary of your geometry to approximate
50

---

an unbounded solution region. For more information on open b oundary problems, refer to the
Appendix.
Surface Charge Density Thisselectionisusedtoapplydistributionsoflinecharge to seg-
mentsorarcsegmentsintheproblem. Unlikealloftheotherb oundaryconditions,thisBC typeis
oftenusedoninternalboundariesbetweenmaterialsoronis olatedsegments. Typically,otherBCs
are onlyusedon exteriorboundaries.
Periodic Thistypeofboundaryconditionisappliedtoeithertwosegm entsortwoarcstoforce
thepotential to be identical along each boundary. This sort ofboundary is useful in exploitingthe
symmetryinherentinsomeproblemstoreducethesizeofthed omainwhichmustbemodeled. The
domain merely needs to be periodic, as opposed to obeying mor e restrictive V=0 or∂V/∂n=0
lineofsymmetryconditions. Anotherusefulapplicationof periodicboundaryconditionsisforthe
modeling of “open boundary” problems, as discussed in Appen dix 3. Often, a periodic boundary
ismadeupofseveraldifferentlineorarcsegments. Adiffer entperiodicconditionmustbedeﬁned
foreach section oftheboundary,sinceeach periodicBC can o nlybe appliedto a lineor arc and a
correspondinglineorarc ontheremoteperiodicboundary.
Antiperiodic Theantiperiodicboundaryconditionisappliedinasimilar wayastheperiodic
boundarycondition,butitseffectistoforcetwoboundarie stobethenegativeofoneanother. This
type of boundary is also typically used to reduce the domain w hich must be modeled, e.g. so that
an electric machine might be modeled for the purposes of a ﬁni te element analysis with just one
pole.
MaterialsProperties
TheBlock Property dialog box is used to specify the properties to be associated with block
labels. The properties speciﬁed in this dialog have to do wit h the material of which the block is
composed. When a new material property is added or an existin g property modiﬁed, the Block
Property dialogpictured inFigure2.29appears.
Figure2.29: BlockProperty dialog.
As with Point and Boundary properties, the ﬁrst step is to cho ose a descriptive name for the
materialthat isbeingdescribed. Enteritinthe Nameeditbox inlieu of“New Material.”
51

---

Next,permittivityforthematerialneedstobespeciﬁed. FE MMallowsyoutospecifydifferent
relativepermittivitiesintheverticalandhorizontaldir ections(εxforthex-orhorizontaldirection,
andεyforthey-orvertical.
A volume charge density ( ρ) can also be prescribed by ﬁlling in the appropriate box in th e
materialproperties dialog.
MaterialsLibrary
Since one kind of material might be needed in several differe nt models, FEMM has a built-in li-
brary of electrostatic Block Property deﬁnitions. The user can access and maintain this library
through the Properties |Materials Library selection off of the main menu. When this op-
tionisselected, the Materials Library dialogpictured inFigure2.30appears.
Figure2.30: MaterialsLibrary dialog
This dialog allow the user to exchange Block Property deﬁnit ions between the current model
and thematerials libraryviaadrag-and-drop interface.
A number of different options are available via a mouse butto n right-click when the cursor is
located on top of a material or folder. Materials can be edite d by double-clicking on the desired
material.
Material from other material libraries or models can be impo rted by selecting the “Import
Materials” option from the right-button menu that appears w hen the pointer is over the root-level
folderofeithertheLibrary orModelmaterialslists.
The materials library should be located in the same director y as the femm executable ﬁles,
undertheﬁlename statlib.dat . Ifyou movethematerialslibrary, femm willnotbe ableto ﬁn d
it.
Conductor Properties
The purpose of the conductor properties is mainly to allow th e user to apply constraints on the
total amount of charge carried on a conductor. Alternativel y, conductors with a ﬁxed voltage can
be deﬁned, and the program will compute the total charge carr ied on the conductor during the
solutionprocess.
52

---

Forﬁxedvoltages,onecouldalternativelyapplya Fixed Voltage boundarycondition. How-
ever, applying a ﬁxed voltage as a conductor allows the user t o group together several physically
disjointsurfaces intooneconductoruponwhich thetotalne t charge isautomaticallycomputed.
Thedialogforentering conductorpropertiesis picturedin Figure2.31.
Figure2.31: ConductorProperty dialog.
2.4.3 AnalysisTasks
Meshingthemodel,analyzingthemodel,andviewingtheresu ltsaremosteasilyperformedbythe
toolbarbuttonspictured inFigure2.32.
Figure2.32: Toolbarbuttonsforstartinganalysistasks.
The ﬁrst of these buttons (with the “yellow mesh” icon) runs t he mesh generator. The solver
actually automatically calls the mesh generator to make sur e that the mesh is up to date, so you
never have to call the mesher from within femm. However, it is almost always important to get
a look at the mesh and see that it “looks right.” When the mesh g eneration button is pressed,
the mesher is called. While the mesher is running, an entry la beled “triangle” will appear on
the Windows taskbar. After the geometry is triangulated, th e ﬁnite element mesh is loaded into
memoryanddisplayedunderneaththedeﬁnednodes,segments ,andblocklabelsasasetofyellow
lines.
If you have a very large model, just keeping all of the mesh inf ormation in core can take up a
signiﬁcantamountofmemory. Ifyouareabouttoanalyzeaver ylargeproblem,itmightbeagood
ideatochoosethe Mesh|Purge Mesh optionoffofthemainmenu. Whenthisoptionisselected,
themeshisremovedfrommemory,andthememorythatit occupi edis freed forotheruses.
The second button, with the “hand-crank” icon, executes the solver, Belasolv.exe . Before
Belasolveisactuallyrun,theTriangleiscalledtomakesur ethemeshisuptodate. Then,Belasolve
is called. When Belasolve runs, it opens up a consolewindow t o display status information to the
user. However, Belasolve requires no user interaction whil e it is running. When Belasolve is
53

---

ﬁnished analyzing your problem, the console window will dis appear. The time that Belasolve
requires is highly dependent on the problem being solved. So lution times are typically on the
orderof1to 10seconds,dependinguponthesizeand complexi tyoftheproblemand thespeed of
themachineanalyzingtheproblem.
The“big magnifyingglass”icon isused torun thepostproces soroncetheanalysisisﬁnished.
2.5 ElectrostaticsPostprocessor
The the electrostaticss postprocessing functionality of f emm is used to view solutions generated
by thebelasolv solver. An electrostatics postprocessor window can be open ed either by loading
somepreviouslyrunanalysesvia File|Open onthemainmenu,orbypressingthe“bigmagnifying
glass”icon from withina preprocessor windowto view a newly generated solution. Electrostatics
postprocessordataﬁles storedon diskhavethe .respreﬁx.
Operationoftheelectrostaticspostprocessor( i.e.modes,viewmanipulation)isverysimilarto
thatofthemagneticspostprocessor. Refer to Sections2.3. 1through2.3.5forthisinformation.
2.5.1 Contour Plot
One of the most useful ways to get a subjective feel for a solut ion is by plotting the eqipotentials
ofvoltage. Bydefault,asetof19equipotentiallinesarepl ottedwhenasolutionisinitiallyloaded
into the postprocessor. The number and type of equipotentia l lines to be plotted can be altered
using the Contours Plot icon in the Graph Mode section of the t oolbar (see Figure 2.33). The
ContourPlot iconis theicon withtheblackcontours.
Figure2.33: Graph Modetoolbarbuttons.
When thisbuttonispressed, adialogpopsup,allowingthech oiceofthenumberofcontours.
In the contourplot dialog, a check box is also present titled “Show stress tensormask”. If this
box is checked, the contour lines associated with the last We ighted Stress Tensor integration are
alsodisplayed,by defaultas orangeﬂux lines.
2.5.2 Density Plot
Density plots are also a useful way to get a quick feel for the ﬂ ux density in various parts of the
model. Bydefault,aﬂuxdensityplotisnotdisplayedwhenth epostprocessorﬁrststarts. However,
the plot can be displayed by pressing the middle button in the Graph Mode section of the toolbar
(seeFigure2.33). Adialogthepopsup thatallowstheuserto turndensityplottingon.
The user can select between density plots of Voltage (V) or th e magnitude of Electric Field
Intensity (E) or Electric Flux Density (D). The ﬁeld at each p oint is classiﬁed into one of twenty
contours distributed evenly between either the minimum and maximum ﬂux densities or user-
speciﬁed bounds.
54

---

2.6 HeatFlowPreprocessor
The preprocessor is used for drawing the problems geometry, deﬁning materials, and deﬁning
boundary conditions. The process of construction of heat ﬂo w problems is mechanically nearly
identical to the construction of magnetics problems–refer to Sections 2.2.1 through 2.2.5 for an
overview of the FEMM editing and problem creation commands. This section considers those
parts ofproblemdeﬁnitionthat areuniqueto heat ﬂowproble ms.
2.6.1 Problem Deﬁnition
The deﬁnition of problem type is speciﬁed by choosing the Problem selection off of the main
menu. Selecting thisoptionbringsup theProblem Deﬁnition dialog,shownin Figure2.38.
Figure2.38: Problem Deﬁnitiondialog.
Theﬁrstselectionisthe Problem Type droplist. Thisdropboxallowstheusertochoosefrom
a 2-D planar problem (the Planarselection), or an axisymmetric problem (the Axisymmetric
selection).
Nextisthe Length Units droplist. Thisboxidentiﬁeswhatunitisassociatedwithth edimen-
sions prescribed in the model’s geometry. Currently, the pr ogram supports inches, millimeters,
centimeters,meters,mils,and µmeters.
The ﬁrst edit box is the Depthspeciﬁcation. If a Planar problem is selected, this edit box
becomes enabled. This value is the length of the geometry in t he “into the page” direction. This
value is used for scaling integral results in the post proces sor (e.g. force, inductance, etc.) to the
appropriatelength. TheunitsoftheDepth selectionare the sameas theselected lengthunits.
60

---

Thesecondeditboxisthe Solver Precision editbox. Thenumberinthiseditboxspeciﬁes
thestoppingcriteriaforthelinearsolver. Thelinearalge braproblemcouldberepresented by:
Mx=b (2.20)
whereMis a square matrix, bis a vector, and xis a vector of unknowns to be determined. The
solver precision value determines the maximum allowable va lue for||b−Mx||/||b||. The default
valueis 10−8.
The third edit box is labeled Min Angle . The entry in this box is used as a constraint in the
Triangle meshing program. Triangle adds points to the mesh t o ensure that no angles smaller
than the speciﬁed angle occur. If the minimum angle is 20.7 de grees or smaller, the triangulation
algorithmistheoreticallyguaranteedtoterminate(assum inginﬁniteprecisionarithmetic–Triangle
may fail to terminate if you run out of precision). In practic e, the algorithm often succeeds for
minimum angles up to 33.8 degrees. For highly reﬁned meshes, however, it may be necessary
to reduce the minimum angle to well below 20 to avoid problems associated with insufﬁcient
ﬂoating-pointprecision. Theedit boxwillaccept valuesbe tween 1 and33.8 degrees.
Lastly,thereisanoptional Comment editbox. Theusercanenterinafewlinesoftextthatgive
a brief description of the problem that is being solved. This is useful if theuser is running several
small variations on a given geometry. The comment can then be used to identify the relevant
features foraparticulargeometry.
2.6.2 Deﬁnition of Properties
Tomakeasolvableproblemdeﬁnition,theusermustidentify boundaryconditions,blockmaterials
properties,andsoon. Thedifferenttypesofpropertiesdeﬁ ned foragivenproblemaredeﬁnedvia
theProperties selectionoffofthemainmenu.
When the Properties selection is chosen, a drop menu appears that has selections for Ma-
terials, Boundary, Point, and Conductors. When any one of th ese selections is chosen, the dialog
picturedin Figure2.39appears.
Figure2.39: Property Deﬁnitiondialogbox.
61

---

This dialog is the manager for a particular type of propertie s. All currently deﬁned properties
are displayed in the Property Name drop list at the top of the dialog. At the beginning of a new
modeldeﬁnition,theboxwillbeblank,sincenopropertiesh aveyetbeendeﬁned. Pushingthe Add
Property button allows the user to deﬁne a new property type. The Delete Property button
removes the deﬁnition of the property currently in view in th eProperty Name box. The Modify
Property button allowsthe user to view and edit the property currentl y selected in the Property
Namebox. Speciﬁcs for deﬁning thevariousproperty types are add ressed in thefollowingsubsec-
tions.
PointProperties
If a new point property is added or an existing point property modiﬁed, the Nodal Property
dialogboxappears. Thisdialogbox ispicturedin Figure2.4 0.
Figure2.40: NodalProperty dialog.
The ﬁrst selection is the Nameedit box. The default name is New Point Property , but this
nameshouldbechanged to somethingthatdescribes theprope rty thatyouare deﬁning.
Next are edit boxes for deﬁning the temperature at a given poi nt, or prescribing a heat gener-
ation at a given point. The type of point property is chosen vi a the radio buttons, and the value is
entered in theenabled editbox.
Boundary Properties
TheBoundary Property dialog box is used to specify the properties of line segments or arc
segments that are to be boundaries of the solution domain. Wh en a new boundary property is
added or an existing property modiﬁed, the Boundary Property dialog pictured in Figure 2.41
appears.
62

---

Figure2.41: Boundary Property dialog.
Theﬁrstselectioninthedialogisthe Nameoftheproperty. Thedefaultnameis New Boundary ,
but you should change this name to something more descriptiv e of the boundary that is being
deﬁned.
The next selection is the BC Type drop list. This speciﬁes the boundary condition type. Cur-
rently, FEMM heat ﬂow problems support the following types o f boundaries: Fixed Temperature,
Heat Flux, Convection, Radiation, Periodic, and Antiperio dic. These boundary conditions are
described indetailin Section 1.3.
MaterialsProperties
TheBlock Property dialog box is used to specify the properties to be associated with block
labels. The properties speciﬁed in this dialog have to do wit h the material of which the block is
composed. When a new material property is added or an existin g property modiﬁed, the Block
Property dialogpictured inFigure2.42appears.
As with Point and Boundary properties, the ﬁrst step is to cho ose a descriptive name for the
materialthat isbeingdescribed. Enteritinthe Nameeditbox inlieu of New Material .
Next, the thermal conductivity for the material needs to be s peciﬁed. There is a drop list
63

---

Figure2.42: BlockProperty dialog.
on the dialog that allows the user to select either a contant t hermal conductivity ( i.e.indepen-
dent of temperature), or a thermal conductivity that is pres cribed as a function of temperature.
If conductivity is selected, FEMM allows you to specify diff erent conductivities in the verti-
cal and horizontal directions ( εxfor the x- or horizontal direction, and εyfor the y- or verti-
cal. If Thermal Conductivity Depends on Temperature is selected, the Edit Nonlinear
Thermal Conductivity Curve becomesenabled. Pressthebuttontoentertemperature-con ductivity
pairs. The program will interpolate linearly between the en tered points. If the program must ex-
trapolate off the end of the deﬁned curve, conductivity take s the value of the nearest deﬁned T-k
point.
Avolumeheatgenerationcanalsobeprescribedbyﬁllingint heappropriateboxinthematerial
propertiesdialog.
MaterialsLibrary
Since one kind of material might be needed in several differe nt models, FEMM has a built-in
libraryofthermalBlockPropertydeﬁnitions. Theusercana ccessandmaintainthislibrarythrough
theProperties |Materials Library selection off of the main menu. When this option is
selected, the Materials Library dialogpicturedin Figure2.43appears.
This dialog allow the user to exchange Block Property deﬁnit ions between the current model
and thematerials libraryviaadrag-and-drop interface.
A number of different options are available via a mouse butto n right-click when the cursor is
located on top of a material or folder. Materials can be edite d by double-clicking on the desired
material.
Material from other material libraries or models can be impo rted by selecting the “Import
64

---

Figure2.43: MaterialsLibrary dialog
Materials” option from the right-button menu that appears w hen the pointer is over the root-level
folderofeithertheLibrary orModelmaterialslists.
The materials library should be located in the same director y as the FEMM executable ﬁles,
under the ﬁlename heatlib.dat . If you move the materials library, FEMM will not be able to
ﬁnd it.
Conductor Properties
Thepurposeoftheconductorpropertiesismainlytoallowth eusertoapplyconstraintsonthetotal
amountof heat ﬂowing in and out of a surface. Alternatively, conductorswith a ﬁxed temperature
can be deﬁned, and the program will compute the total heat ﬂow through the during the solution
process.
For ﬁxed temperatures, one could alternatively apply a Fixed Temperature boundary con-
dition. However, applying a ﬁxed temperature as a conductor allows the user to group together
several physically disjoint surfaces into one conductor up on which the total heat ﬂux is automati-
cally computed.
Thedialogforentering conductorpropertiesis picturedin Figure2.44.
65

---

Figure2.44: ConductorProperty dialog.
2.6.3 AnalysisTasks
Meshingthemodel,analyzingthemodel,andviewingtheresu ltsaremosteasilyperformedbythe
toolbarbuttonspictured inFigure2.45.
Figure2.45: Toolbarbuttonsforstartinganalysistasks.
The ﬁrst of these buttons (with the “yellow mesh” icon) runs t he mesh generator. The solver
actually automatically calls the mesh generator to make sur e that the mesh is up to date, so you
never have to call the mesher from within FEMM. However, it is almost always important to get
a look at the mesh and see that it “looks right.” When the mesh g eneration button is pressed,
the mesher is called. While the mesher is running, an entry la beled “triangle” will appear on
the Windows taskbar. After the geometry is triangulated, th e ﬁnite element mesh is loaded into
memoryanddisplayedunderneaththedeﬁnednodes,segments ,andblocklabelsasasetofyellow
lines.
If you have a very large model, just keeping all of the mesh inf ormation in core can take up a
signiﬁcantamountofmemory. Ifyouareabouttoanalyzeaver ylargeproblem,itmightbeagood
ideatochoosethe Mesh|Purge Mesh optionoffofthemainmenu. Whenthisoptionisselected,
themeshisremovedfrommemory,andthememorythatit occupi edis freed forotheruses.
The second button,with the “hand-crank” icon, executes the solver, hsolv.exe . Before hsolv
is actually run, the Triangle is called to make sure the mesh i s up to date. Then, hsolv is called.
Whenhsolvruns,itopensupaconsolewindowtodisplaystatu sinformationtotheuser. However,
hsolv requires no user interaction while it is running. When hsolv is ﬁnished analyzing your
problem, the console window will disappear. The time that hs olv requires is highly dependent on
the problembeing solved. Solutiontimes are typically on th e order of1 to 10 seconds, depending
uponthesizeand complexityoftheproblemand thespeed ofth emachineanalyzing theproblem.
The“big magnifyingglass”icon isused torun thepostproces soroncetheanalysisisﬁnished.
66

---

2.7 HeatFlowPostprocessor
ThetheheatﬂowpostprocessingfunctionalityofFEMMisuse dtoviewsolutionsgeneratedbythe
hsolvsolver. Aheatﬂowpostprocessorwindowcanbeopenedeither byloadingsomepreviously
run analyses via File|Open on the main menu, or by pressing the “big magnifying glass” ic on
from within a preprocessor window to view a newly generated s olution. Heat ﬂow postprocessor
dataﬁles storedon diskhavethe .anhpreﬁx.
Operationoftheheatﬂowpostprocessor( i.e.modes,viewmanipulation)isverysimilartothat
ofthemagneticspostprocessor. Refer toSections 2.3.1thr ough2.3.5forthisinformation.
2.7.1 Contour Plot
One of the most useful ways to get a subjective feel for a solut ion is by plotting the eqipotentials
of temperature. The number and type of equipotential lines t o be plotted can be altered using the
Contours Plot icon in the Graph Mode section of the toolbar (s ee Figure 2.46). The Contour Plot
iconis theicon withtheblackcontours.
Figure2.46: Graph Modetoolbarbuttons.
When thisbuttonispressed, adialogpopsup,allowingthech oiceofthenumberofcontours.
2.7.2 Density Plot
Density plots are also a useful way to get a quick feel for the t emperature, ﬂux density, etc., in
various parts of the model. By default, a density plot denoti ng temperature is displayed when the
postprocessorﬁrststarts. (Thisbehaviorcanbechangedvi aEdit—Preferencesonthemainmenu).
However, the plot can be displayed by pressing the “spectrum ” button in the Graph Mode section
of the toolbar (see Figure 2.46). A dialog the pops up that all ows the user to turn density plotting
on.
Theusercan select between densityplotsoftemperatureort hemagnitudeoftemperaturegra-
dient or heat ﬂux density. The solution at each point is class iﬁed into one of twenty contours dis-
tributedevenlybetweeneithertheminimumandmaximumﬂuxd ensitiesoruser-speciﬁedbounds.
2.7.3 Vector Plots
A good way of getting a feel for the direction and magnitude of the ﬁeld is with plots of the ﬁeld
vectors. With this typeof plot arrows are plotted such that t he direction of the arrow indicates the
direction of the ﬁeld and the size of the arrow indicates the m agnitude of the ﬁeld. The presence
and appearance of this type of plot can be controlled by press ing the “arrows” icon pictured in
Figure2.46.
67

---

Figure2.50: Conductorresultsdialog.
2.8.1 Problem Deﬁnition
The deﬁnition of problem type is speciﬁed by choosing the Problem selection off of the main
menu. Selecting thisoptionbringsup theProblem Deﬁnition dialog,shownin Figure2.51.
Theﬁrstselectionisthe Problem Type droplist. Thisdropboxallowstheusertochoosefrom
a 2-D planar problem (the Planarselection), or an axisymmetric problem (the Axisymmetric
selection).
Nextisthe Length Units droplist. Thisboxidentiﬁeswhatunitisassociatedwithth edimen-
sions prescribed in the model’s geometry. Currently, the pr ogram supports inches, millimeters,
centimeters,meters,mils,and µmeters.
The ﬁrst edit box, Frequency, Hz , denotes the frequency at which the problem is to be ana-
lyzed.
The second edit box is the Depthspeciﬁcation. If a Planar problem is selected, this edit box
becomes enabled. This value is the length of the geometry in t he “into the page” direction. This
value is used for scaling integral results in the post proces sor (e.g. force, inductance, etc.) to the
appropriatelength. TheunitsoftheDepth selectionare the sameas theselected lengthunits.
Thesecondeditboxisthe Solver Precision editbox. Thenumberinthiseditboxspeciﬁes
thestoppingcriteriaforthelinearsolver. Thelinearalge braproblemcouldberepresented by:
Mx=b (2.21)
whereMis a square matrix, bis a vector, and xis a vector of unknowns to be determined. The
solver precision value determines the maximum allowable va lue for||b−Mx||/||b||. The default
valueis 10−8.
The third edit box is labeled Min Angle . The entry in this box is used as a constraint in the
Triangle meshing program. Triangle adds points to the mesh t o ensure that no angles smaller
than the speciﬁed angle occur. If the minimum angle is 20.7 de grees or smaller, the triangulation
71

---

Figure2.51: Problem Deﬁnitiondialog.
algorithmistheoreticallyguaranteedtoterminate(assum inginﬁniteprecisionarithmetic–Triangle
may fail to terminate if you run out of precision). In practic e, the algorithm often succeeds for
minimum angles up to 33.8 degrees. For highly reﬁned meshes, however, it may be necessary
to reduce the minimum angle to well below 20 to avoid problems associated with insufﬁcient
ﬂoating-pointprecision. Theedit boxwillaccept valuesbe tween 1 and33.8 degrees.
Lastly,thereisanoptional Comment editbox. Theusercanenterinafewlinesoftextthatgive
a brief description of the problem that is being solved. This is useful if theuser is running several
small variations on a given geometry. The comment can then be used to identify the relevant
features foraparticulargeometry.
2.8.2 Deﬁnition of Properties
Tomakeasolvableproblemdeﬁnition,theusermustidentify boundaryconditions,blockmaterials
properties,andsoon. Thedifferenttypesofpropertiesdeﬁ ned foragivenproblemaredeﬁnedvia
theProperties selectionoffofthemainmenu.
When the Properties selection is chosen, a drop menu appears that has selections for Ma-
terials, Boundary, Point, and Conductors. When any one of th ese selections is chosen, the dialog
picturedin Figure2.52appears.
This dialog is the manager for a particular type of propertie s. All currently deﬁned properties
are displayed in the Property Name drop list at the top of the dialog. At the beginning of a new
72

---

Figure2.52: Property Deﬁnitiondialogbox.
modeldeﬁnition,theboxwillbeblank,sincenopropertiesh aveyetbeendeﬁned. Pushingthe Add
Property button allows the user to deﬁne a new property type. The Delete Property button
removes the deﬁnition of the property currently in view in th eProperty Name box. The Modify
Property button allowsthe user to view and edit the property currentl y selected in the Property
Namebox. Speciﬁcs for deﬁning thevariousproperty types are add ressed in thefollowingsubsec-
tions.
PointProperties
If a new point property is added or an existing point property modiﬁed, the Nodal Property
dialogboxappears. Thisdialogbox ispicturedin Figure2.5 3.
The ﬁrst selection is the Nameedit box. The default name is New Point Property , but this
nameshouldbechanged to somethingthatdescribes theprope rty thatyouare deﬁning.
Nextareeditboxesfordeﬁningthevoltageatagivenpoint,o rprescribingacurrentgeneration
atagivenpoint. Thetypeofpointpropertyischosenviather adiobuttons,andthevalueisentered
intheenabled editbox.
Boundary Properties
TheBoundary Property dialog box is used to specify the properties of line segments or arc
segments that are to be boundaries of the solution domain. Wh en a new boundary property is
added or an existing property modiﬁed, the Boundary Property dialog pictured in Figure 2.54
appears.
Theﬁrstselectioninthedialogisthe Nameoftheproperty. Thedefaultnameis New Boundary ,
but you should change this name to something more descriptiv e of the boundary that is being
deﬁned.
The next selection is the BC Type drop list. This speciﬁes the boundary condition type. Cur-
rently, FEMM supports the following types of boundaries: Fi xed Voltage, Mixed, Prescribed sur-
facecurrentdensity,Periodic,andAntiperiodic. Thesebo undaryconditionsaredescribedindetail
inSection 1.3.
73

---

Figure2.53: NodalProperty dialog.
Figure2.54: Boundary Property dialog.
74

---

MaterialsProperties
TheBlock Property dialog box is used to specify the properties to be associated with block
labels. The properties speciﬁed in this dialog have to do wit h the material of which the block is
composed. When a new material property is added or an existin g property modiﬁed, the Block
Property dialogpictured inFigure2.55appears.
Figure2.55: BlockProperty dialog.
As with Point and Boundary properties, the ﬁrst step is to cho ose a descriptive name for the
materialthat isbeingdescribed. Enteritinthe Nameeditbox inlieu of New Material .
Next, electrical conductivitiy for the material needs to be speciﬁed. FEMM allows you to
specify different electrical conductivities in the vertic al and horizontal directions ( σxfor the x- or
horizontaldirection,and σyforthey-orvertical direction.
Thenextpairofboxesrepresents therelativeelectricalpe rmittivityforthematerial. Similarto
the electrical conducitvity, textit εxrepresents permittivity in the x- or horizontal direction, andεy
forthey-orverticaldirection. Ifthematerialisalossydi electric,thisvalueisconsideredtobethe
amplitudeofcomplexpermittivity.
A commonway ofdescribing lossydielectrics is viathe“loss tangent”. Losses can be consid-
ered asresultingfromacomplex-valuedelectricalpermitt ivity. Ifthecomplex-valuedpermittivity
isdeﬁned as:
ε=|ε|(cosφ−jsinφ) (2.22)
Thelosstangentisthen deﬁned as:
losstangent =sinφ
cosφ(2.23)
75

---

For material that are also conductive, FEMM combines the deﬁ ned conductivity, permittivity,
and losstangenttoobtainthecomplex-valuedeffectiveele ctrical conductivities:
σx,ef f=σx+jωεoεxe−jφ(2.24)
σy,ef f=σy+jωεoεye−jφ
which takes into account resistive losses and addition diel ectric losses due to the deﬁnition of a
non-zero losstangent.
Conductor Properties
Thepurposeoftheconductorpropertiesismainlytoallowth eusertoapplyconstraintsonthetotal
amount of current ﬂowing in and out of a surface. Alternative ly, conductors with a ﬁxed voltage
canbedeﬁned,andtheprogramwillcomputethetotalcurrent ﬂowthroughtheduringthesolution
process.
Forﬁxedvoltages,onecouldalternativelyapplya Fixed Voltage boundarycondition. How-
ever, applying a ﬁxed voltage as a conductor allows the user t o group together several physically
disjointsurfaces intooneconductoruponwhich thetotalcu rrent ﬂow isautomaticallycomputed.
Thedialogforentering conductorpropertiesis picturedin Figure2.56.
Figure2.56: ConductorProperty dialog.
2.8.3 AnalysisTasks
Meshingthemodel,analyzingthemodel,andviewingtheresu ltsaremosteasilyperformedbythe
toolbarbuttonspictured inFigure2.57.
Figure2.57: Toolbarbuttonsforstartinganalysistasks.
The ﬁrst of these buttons (with the “yellow mesh” icon) runs t he mesh generator. The solver
actually automatically calls the mesh generator to make sur e that the mesh is up to date, so you
76

---

never have to call the mesher from within FEMM. However, it is almost always important to get
a look at the mesh and see that it “looks right.” When the mesh g eneration button is pressed,
the mesher is called. While the mesher is running, an entry la beled “triangle” will appear on
the Windows taskbar. After the geometry is triangulated, th e ﬁnite element mesh is loaded into
memoryanddisplayedunderneaththedeﬁnednodes,segments ,andblocklabelsasasetofyellow
lines.
If you have a very large model, just keeping all of the mesh inf ormation in core can take up a
signiﬁcantamountofmemory. Ifyouareabouttoanalyzeaver ylargeproblem,itmightbeagood
ideatochoosethe Mesh|Purge Mesh optionoffofthemainmenu. Whenthisoptionisselected,
themeshisremovedfrommemory,andthememorythatit occupi edis freed forotheruses.
The second button, with the “hand-crank” icon, executes the solver, csolv.exe . Before csolv
is actually run, the Triangle is called to make sure the mesh i s up to date. Then, csolv is called.
When csolv runs, it opens up a console window to display statu s information to the user. How-
ever, csolv requires no user interaction while it is running . When csolv is ﬁnished analyzing your
problem, the console window will disappear. The time that cs olv requires is highly dependent on
the problembeing solved. Solutiontimes are typically on th e order of1 to 10 seconds, depending
uponthesizeand complexityoftheproblemand thespeed ofth emachineanalyzing theproblem.
The“big magnifyingglass”icon isused torun thepostproces soroncetheanalysisisﬁnished.
2.9 CurrentFlowPostprocessor
The the current ﬂow postprocessing functionality of FEMM is used to view solutions generated
by thecsolvsolver. A current ﬂow postprocessor window can be opened eit her by loading some
previously run analyses via File|Open on the main menu, or by pressing the “big magnifying
glass” icon from within a preprocessor window to view a newly generated solution. Current ﬂow
postprocessordataﬁles storedon diskhavethe .anhpreﬁx.
Operation of the current ﬂow postprocessor ( i.e.modes, view manipulation)is very similarto
thatofthemagneticspostprocessor. Refer to Sections2.3. 1through2.3.5forthisinformation.
2.9.1 Contour Plot
Oneofthemostusefulwaystogetasubjectivefeelforasolut ionisbyplottingtheeqipotentialsof
voltage. Thenumberandtypeofequipotentiallinestobeplo ttedcanbealteredusingtheContours
Plot icon in theGraph Modesection ofthetoolbar(seeFigure 2.58). The ContourPlot iconis the
iconwith theblack contours.
Figure2.58: Graph Modetoolbarbuttons.
When thisbuttonispressed, adialogpopsup,allowingthech oiceofthenumberofcontours.
77