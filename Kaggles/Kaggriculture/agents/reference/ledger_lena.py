# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Rayk Kretzschmar
#
# The MIT grant covers the code in this file -- the market/SELL layer and the scheduler.
# It does NOT cover the base85 `_TRACE` field plan below, which is the shared public meta
# line reconstructed from public competition replays and is not the author's to license.
# See NOTICE, and the "Provenance" section of the dataset description.
"""Ledger Lena -- tier 7 of the Kaggriculture reference ladder.

Meta field plan with a different sell-ordering trade-off.

STRATEGY
Same meta field plan and the same reordering idea as Slotter Silas, tuned to a different balance between selling premium goods early and keeping staples flowing.

WHAT THIS TIER TEACHES
A useful A/B against Slotter Silas: identical production, identical strategy in outline, measurably different results. If you want to know whether your own market layer is any good, these two bracket the question.

FIELD PLAN -- READ THIS BEFORE REUSING
This agent does not use an original field plan. It executes the shared public
meta line: `scripts/cross_team_identity.py` over 530 downloaded replays finds
identical 712-turn farmer/hand sequences played by large groups of unrelated
teams -- one group of 29, another of 15, another of 8, with 104 distinct teams
appearing in at least one shared plan. No single team is credited because the
line demonstrably belongs to none of them.

What is the author's own, and what separates tiers 6-9 from each other, is the
market layer: which product takes the earliest slot in the order queue, when to
hold, and when to liquidate. Their head-to-head ordering differs from their
standalone bank ordering, which is the whole point.

Measured end-of-season bank: about 164,540 coins against the built-in
`starter` baseline over a 720-turn season.

This file is self-contained. Rename it to `main.py` and it is a valid
competition submission; or import it and call `agent(obs)` directly.

Part of the Kaggriculture Reference Agents dataset:
https://www.kaggle.com/datasets/raykkretzschmar/kaggriculture-reference-agents
"""

import base64
import copy
import json
import zlib

_TRACE = json.loads(
    zlib.decompress(
        base64.b85decode(
            "c-rk<O>Z1oa{Mnm^T7V%hi_b|cScx_C{UCe>j5zsz-t&V)`zighX1=YVs~{_Wn^SzzSpGaom->W?0VlXGcq#r=l?nTw_ktz``>;$`=_7JKHYx)eD-vH_V2&`=fD2f*9Tue{{7eA{^M`|{q^(DXFq;;*na)%=)<4B{PmaHj~{-zy*oQUdw0J(J6{|gf8K82e|`AV_U``U+4<${@$Sd%?c@IO=k49y@zKIQTA^<}{qOm><$wC};qLt}U)%rq<y+f^F8qA9+kSrh*4mHv505{dJxx3Hd!s%*+`s?w?s3+xL@)RMwwbr;(}#C|`SNM>U!!L2TXR1C^xRaTflIGl^9J1AzT58qI(hqiygIew^N-u@C)AF^Kpg*b)R@orU-qxI&6+(CTD3Y(-mDdW{(ZJ4Z=O!jayky%+x^0k2V^0v)ZvxGSdAO>?$%7l@aXx2w0vjpJp343eqYzf$H!r-PT&1}AdFub|MGOreI32q$L&M-yU`Mxo+s`?e;!mkq{BgQTyLly)A<`30M=Q!yhbk~gAC6la4Px(G;i{(Vfzt4>wf$zXrlH#kY;N3*8On9H8)Jf@FBM%qCK`B?dQKw+OVG_G$ZaDk@bHVGdStT0Udo(&l2U<vqNkLcJ_hvg^b#KPb-5r`?*?|?W(c^K1?Yb@8?f!3e6ze6C-~WtdSj~5BPCkm~kE2LIyY<wBxcEhHBm%ICy$@m%=Rsj%2n~QVVw07yHDX&iYba3+oasN7GM!>L<)7b&_UQe0Ya(^BG*0`~}<+JlZ<<cX!)&kH7qR`|$YT?!&)KmPE>yU$wRg+*<VRE_OKRdFzWt_9T4)v@>&E!oNQ|LbV08PFb?=AMQWtuNbw@z6b1s<2m{4CEGJp@(>b-B6yMRnpHX^-2k&6KAdR019|($^Z>occ44$z3panR<&`1Mv~Ry<utQ-RsN3rHVwnLyu<6H_gExggcr;u3{2py!Jhn;$kFR+C+v~P3JNK0z9LAu~VLN{0*WfAKVDErmTlTkhWUER9Ely|)sVK(H39X{0<G!!mB)JoP4X7U0p*Hh5FMsyNMT8%eoN8*;#8_DCb?YN9&8<%%Eb9HM^@SiyMFZ_<l-pryFej*~HoViALdv~kZMNg6fZoi}{QMonP+jZOu%65h<*TRA-Wy(UbZzW7qBm8|K41i;Q1h=x-@|?RRkm+o03v5-&W*Cv4-a$TTd=hsKKfs8_lIYzQTkcgy6bDjO-!`FoP$`wc?eUyILfv72R7q|*%*@z0xbGPY`uBIHcwrFG|Bo)FIC4L1Q!rBLg3c9E}>uDtwR^w(O~&a4-D^g<{}NLyg6&p2hNHRAB9nvxtNLedkAq6_LEGd7dHdDU_??!PG<9Ir&K>vP=vkyun;@oe+y)%y(%QwWRrA(1NVl=+O>WcFA*)RnYgDnE&GLaD+VMRk{)&=orcrlhd<sv{B!iV6C#I>uGoi}g7hm)?G?y=UgrjSQi<bY4H%!=f&kUw?Z-z$<J__M{P=LY`_uN};jfl~snh+Cr*LTM=nW1Z5PZ>XZ-EDh_JFl&bBmPGtj51IS_s?E9y=*q8Qg4kesA8VMCS<Cki6DD0V9zcQ@h+b<&v^lL))7I*T5qRtydP+cYiNsA4_j&>jaA?_vr*N@-5E?Sg)e-y=()j-ACQrmt5Ces%h4eKK#(aK|#NR=z5g<@;xvO`y|Mm&Zu6U$f&j#`U{%WHjAi)sMkhj*vn2cS+Y~>7#+{UdEyyD@%p(t_PxjCrhrrz6QMMJ1MC6>9Y#h~F7jXM5ceGX?5R%OIj%pDYu2el!xHmRxRlQcOkH3@XS-2IuNmiFO!Cc|36pjZ2hVMor$z>#1npD9qXFb+Aq)2MOb3DSPQq89e<DX@N#L_KUg)Wbm@ohPU94gIWcHyah75AkU&HXdYDHpUj;Dk+o+^{337E{d3{}H2Flxbt*=jifcrIb+3i+ud33qIEpuBTA5vhI$fbQ>1lQOh<YVZKSDm2m?;uGW;;Nf~5lw()A4>$KAAuzxf;qRf#STHoT&XVk19pnUDPmdQ-8cmizO361fGz{Nq_xE?~O3Umb;D@*fnH`A$v;l7>Tm)e8pGdHPaz$nhOZgZ~xJJkzs&yTN#xDiA0lq9O<ls{Ys?fiXL{=S<_+(`-_iWbO*&W*H`~?ktvxJu9n>7MP-wdx+3ytAqM*6-@cefwk_psO*lvm;hN7-uQ;P2WKy0SBS(HDOgA#Z&IHqC?<SCWbOD?NRLm`job<C|Rwp9c*`sWNX1)o5V|S}-ofzgGl<sDJ_R4<PN;{aVd<W=tBkc542K5}`k*?1CA2q<#@<5>*zb6dqL*7wsqyS2KHkOqWr%5CKqyxI}VPbldc%W}7l3fjKexLCq*0p`E=ISka}StZ;a!+c7LgE1r~EdW)L682}h0?nH~UmC!EageWL>)1gs*={D96YtXl(u{yAt8OYyr*0gq^wPQX6k}Ilo<06s&n`@w`Y^FEVO#Af<v^_J~pn>OM-qs5`pLH*^LAY3U^Oha_R7fjr$|cQ=qv&i7*H<MJCHtR;WQz}Xf7vg@lY69)-HSs#Sv@<C!NyR7qJL`~Ms8&YY%5W9u1CTN3Sr?!0XTnn#8_-Iw1F(TMTVk~oE(wtRX`=s7u!~1va_H`hStY;bcAEC#@8jbD6!)wL0uQNm~ofbq5}?+a79Oxq=$%S<Tx*@;kZ1R>janVQ9qbx#pwQkm*oO{EW55^_A0<h(v4;y1X$3ZQB;=58h^R0qeTLm2<|?{-!wa6zCf0eqZEv_L@KpwJG{P+ECzc@c^flmsvTx<0ch|OM)Qu3=G>1CZ4IrusKNa3FrI4Ea=N1J4kQNVdBm>3pvP==yYWz^y&{%Nhmb~V=ZTV4nh$(Qv_LhCu);y5I1M~Sx5QsIbLydiwIxU!%LpI#$?Q<d%_gulqP^Rh_KIFY(G4ciCV*T*Py?b6o#?KMt4`2?T~lr0zm6z?V-CYwC{?F_9I`kusxcxUQQ`o6XrL_cYX-1yi@-0s!8n}S?6G&#@(-s8=Lgfq+Y@#2h=<%d{@bbA4XC`#L)Q5pjpYb{^EY0P*vNkW;Rgqis&X)5Yy%X%s{uHR2$lj<<=jGHw_JR!mZyH4EW`|_%z@o}?uM3%HhYD?4pw*|LSiHRp=p{|_*$g`(LkVty7Y)ff7l+=LH{-tokyD6`PM9(wn#@MH35=JP)}of(DXQpZm>+pZ#?j|Q+Bg?ZfG`3G&PjMuNHDyX$3o}1xp=Wem&bhqJu#bzE+DnN~e;d3K_PRUl&CcMoKWVtsYJq0+R+=zwKNZLJdQQQbERFsOLdy%Yw6=5`E~wf>vvC{uwBOmKViBn8U4=SJT4yHyH?;4k{-#vP_0H!6GF$BEXw8%`#D0$16r0KzBqzR~yBq${%4rubSu{ZQ#iAO@bpdI{jUsBjbn6r7lg{MSosP$jC`&G@lv;$*ebE&qV!!Y$UI)Ye(H1h=>dyBDTtoGj~o@8j>WmCi6Q)@<&<i#~A=S&{5`xKK>vs6puHt6h!}lW`cCk1t2YCIr$9k;XYCm7(`13MUtX;FWE&u@<wZEG@zA0KNL?cw}&ecH0A@)^n9#TivFdkSQE8B!?iA>Y!y*~0!GKZ81xBnI*K7u=8kgu0AL+z9@J22B_jfCcAQ(U7Y0hnz=qXeNN6zziw0$AT^<aSr1v$+<lg3((}LQ9mfAUC;2CFZ5;iee<ir_eleV}d^_g@91->h3BW+^BxTABp$Ib~%|JIT})0zs@Z;zV_Fwxahk`57F!c5|fDPpn|G$ps?u%5gu;#EqA1w=|vdcL%r{B;;f)GwPkABP{haz=$X=*w3`J63N5?Z~JDzb3K)e(2jOUbgr4=7lhhBI$!0ZqldI^FNTx(JTu)E!!qm<%Sv{tqC$d6C;F6ZvA8gL7$@?8DW43^w3o`=nlM*E>mNie_eEhN+t-o0qwKHqn1Hd07>kbPjO}3X)qbs6T>4bF2dp;7J{RMos>V!;3=-<M|C3@#aGT_p!8;zcL4&UB-qS^8yz}B0USZwCP0v=nzucLGTJT7IkZPK3*$SBM1Z#O-mQq;M5J+6+mbOLKq{J0-@X~jv(Sl1nB%Mu8oWDdNUBU4wgIU|d`L`8GZtX_S$iTMaOXJW=4x7Gz!LQUWJe5TtZ1{u5Xh!>v%HkVA_-?Notnd-D_YW1t6-pEgtXNni=>GS$6C%yKgd*9SBb31GGdjYxU~v^Cl}MMt@gGmr<*>246kF3ZQYZzPxLS?bERJtu1L16h}XO_??i91U0;ILM}7M&=V-k3#v;ehLK!#B8XtPSCrugilmemzVi}$&tRcCkZAK_(krL#_o&g(AnvE13G>&+|r2WeaokMSX2F&*eg0XW~X5>iP<?EY-dX>+c5%x@|7!y0fG`H$nhcx&7$cPMpF}M4TIL?r!qFSD|1E{$gB0`fGSYY2xPhqpNxvWs|f$eAqTM`4&%aMT?A<Jh#Ch=Cmlil@BP9d{LkE<zgrw|be((Mzm2D_$|lN8h<SZ!i9e&}6<NsdSGl~DtjTaVw}%-<g)KscQZRR`2u$DA<Fs!jNj%FObfi_T;0F_|NBzp}Y9Xaa}=84DRNo)Q_Bc5f`l&mQl8x_!L2%Kh8}%~f-5n8akS$3=kaopGiPXc?Dh(=O8^`pahZ*>dzG?k`H^1T~0J)0#$e_&ja|Bi^K>M#<Vkco-?dy2VAtnFOuoH&<5}Poqjs#q{K-Z#-41(}JW4Uz}b)rhrkc|A4685Ja{9E)c4cP)q@!azud}87g7gF)(+vkg;Ay55)Zl29@w9DAz{f|I`th#IgW`$HqE$v^3Y{TqR%}5a?&|aYl~-!$Vw;c!n%8Ll6vrasV60uKwwzTM3e6@fg&GdAAZ!Gv#FQ->LLY*5oAk3ngi>;PW<Oy3@h|&$hVW-|}ijTcJ!So0GiS&(d@vqn<0u6lkCzl4J6{g~N!S_b4Kd`r!)9kafkn+^{h~7@cQ|fp$=ckR{P|-Ow~~5BxE4sY}>FpHj>rba#*uvo{ClqMT|Xb`ppSSfg1%5}~HDYRcDnN_<C%ydB0S(Y1_hl`onbWAk+u8N5-XPSY72fURK-x6hx~7Y5(hJvIl$qMpcdxe3`ezfRB?>e#rmd|iiw$mR?_5yczwpN;!;nSmeCSxA65nk1J^^&QV8wj|blNmmynJ++07H6dS6XTxpPyyn&U>FGebyvj@?7`8esP?SI<D$p2}5=jWbz6PPo`tBaND_23Q1I-D;dxgXTt{J2!*yZx|xf@#OI;GJODj2wa0Z7`GS?8AladWr4&$6U+t1|P*T~)W}vPAp>GZCmH9`nGO7U!g+NF^3TpBF2q_+onrW|C!Om#>t^We=*8=|CgPNT-f5Cx+g#>?-j^HC9=alAbLL(gQ(vd&+RJZV^3FvXKB9j6Q*{(HtWsF*0NYO!nWmxcXJAo(TVB@h)9j%L}xmOQ%5|vL4*x$cB*GM{cx;NvElLQTQwd!*dCx<V+ON(5=fc*297JytL_y6v!FAj%qZ-%x3Nu&(a&?Eyh?WfFv1LWmeZrA}!O^tg_Tq#2h3EX*Sb~ABttsXt>?j*n^H}X=(l*Cd~tYKGRl~Mv`R?6O_Ez%AGIU1uz+u{T3swWXWDVCE997Mp9JL=3hG?_FHN*x|WSh%8abpOQ`9}CkVb)^55c3GONI_o>+#Osk-$eTNSEXchnAtjSKo)pk38rBvb#Sy?cc^*DM_+N4Jt;q?;Z+Wi^?AA5P-d3XBxZ6%C~C)XdU~C*Jm(G-v0$PSv91D`v=JonN*PL(GqP*c9<&>^LevRKar^NK4UL0D?>^awn3z$W}=#Bc+<QuDUM<0l|<^DOe{f*lq!E_E6`9gICcUXR5O#1#se9Ac7LQP)!t#bCSraiNs3?hXs~1YDugdJ!!2R8%nt4r8;pyVGNwz@ZoOjZ#th1lgoJxPXo)bIl6C*8xo`+?QtJn-zEVF2TZ(-t|4Nj0JX5FhP(@%+6m#xQxtBb9Rom|z{XhS#+#v#Tzm?AZI&xF1BP<ToQDPiNL^ApoFOtfI49;o%cU{}mQk*47W)GmK%nbNjK0Jy=ZmD<x|!yQOT{te=1vXRcty$zI6$LA`PxZyC%|!d&8L&*%!y9psgWH%0$lM)cfenaA=HB8P%lplGFGd6_eXAY_MVLaD)O3Q3PiXvuzgM`7-HA7V|1Fkf9=s^P6Ft#YVJh+X;)D6D&jmW(@xH0bL!tURgWl@b9D-vm&yvT;J)sy3qm*mb4xT>DyUVYC=ioItanc3#A3mmqMZIB#k^5{0#^1)z)t#5*EEe9S}reWw@wtHE(FaobY#*Qi_Y9(nY7VFk|?jP&V|fUXAbK~B9St1to?f8V$nGPI<V;)3`jiyLYm4|fefO69SI6BgBYlG4<&JF7`!gfojCbuu~Jd`N<1k^&97V`ukp^xW;xS{Zld%g%dHiK*F|VDz{sjvhZc&Z_PCnLDdxu<5g1|F=BYP^g!}wt;~+cNFPr!kf&iO-{G3`|#rF*2&}G_&+_1cg11;>ekejef{G`+;{RIPRT1-UohF&DuOOo3TS20Rh(4~}nRO#YbUiO1hQSGFY1nfp{wN<7r^3oIYfH|F;ObUrwn=Y4}rlucOa=#Z&w^yYkEoA%=MW#gbSmTS(iIY;c7(tJwDGIU6l2nvYxZ(yUWdu;0ak_5+Gpy2lNZ?0hs<yFj?ln~s&M2vi1qpB%p_BnvY8@*QOTre=(l^1Qjm}zO2O^6rOSw<ne-VQDBwLG#?3-0K&>qnJf+uXA2*eD+L|oZPKAt|hNu=Le_YQcTAZb(McH!Je&V88-#LCNjNMsTQ0Gt$L5fEAmw;h)a=PgV7f{PNS2D`k=nFJXrOcE@JIAWIzRM}O*?s$;Arxn7Jl;UbkqXWdk((XjXAieG`C2E;$wIfzJG}5b5Aa1~6B2-C#1!HBmiXx^I;+v@Vr&8ix{gL?f2Ro=a%L}`I*RRYG3VmgzJ{*;d_+HY#0HcQBF`>zS&GQ*2gK+)w{33{PCx{73>7dn9SJIJ2^wP*4q2SKu1=7G^;sA`I1LR3a+B-x|ng~Nu+}oiD<*pPYC$GvuO%zS9x+HoO6IPg!n#r|FXz56#Bd8U}^u`<<*Y$;9U%vjx!#$M6-WWeysXn3!`EVU0ifu^HXsz(%GVZY?4X!4Q;)6!09Y7!e51e0KXlT~5NnactjbdmU{ncC8lH%1E-tkpz3;ni0b1={N&q4kX^-@XdA6~a|T}zGErsd@4bo88-YeA$K=ho_xdB;;@ixaBu^qc@7Bd49J#_+;L4$n=w$po8^7k{vGGl{4RmC7{ifK`pus<BZ0WeNLe!aE6i$hkpe3|kYk=?H?==@yj>Ll+?c$1BWA(pOAGJ<z2iB1q$%bP2*1WsEC^D4t)jNT6E)R8W{?uK{_HdfhV9<+Z6)709bs*|h6dAWn7HHOgm|<dN|vHS}b{0zE2q18S|~B8A>D1tTJQY3CWq4d<d&6syveorCm<gq%x<Qgi2yah3qIm>{&BA(o}+Y7PtgNbCqR?gcG+q`j_VSNNCY<>=edxyikF(v@lH;bJjDYTvNsUc2}`=%FO*u9Ee!bM4G+u%zPYy=Z|)SVc0b?j;c(@)3|l6LTpnRS2gj%0}D9NUo9+b;YSa`7P@RI&e*KO-+lhZ!h^q8jk5U3>^@(F>&5vFt=)cEKO67GC8V;sWY^!5EC$4I_PUA?|5En&MpjmGE!!T-HOBji!enoED-@*!ReuS;^U!C5dOq?sFcE~SGd=*KRv}iF)f%PqqNCcmA3@j2vH|#+r<%;l2Z?%{&N;Wkn7&^HY&yYVmFX;zQ$|*GE=FP4l1364DYWe*=xTSylg{Y4J>Y6C<756G^@9mZ<q*~eXlu)nwsPP!-PXIAA73@Rsog%s^=h>E?5vr_^w`J8Q1EoA;+7Oq$(z4xVKVGwA1F7GPH@|h}erS6xE~FTQsUlF}+evxpHB>D%lMXQz-R`TeIAaBk=TekH&tq=qa<>c69Ogscy#_Za)n6Z6UIy^hT89G?iFFI@EzCCK$dlNRUX<715&_WSh}UXJ;+=5<bd2NN0XH<tPmlPLs=iM#me|2+Bz)kvWYEyUFnA^Ny>Hq|6O=^t7D$t_X^gR{B|#a>Y0*u$4<Y<iJ01{XH;_O)kqyXXsZ|tdV1EjMK|Pz_apx;eoZ5QpX8vN?Q~`Z*>`NhK)G*GBDp~S#ClkkF=0fDb6ln8e<DN3L*u{t<l#m511E(k8qxZ3VIsonas|@7Li-NM5bTVmMQS|0`f&lsJt6h3Jmz$U{47==I<2*;^e6m>H`MJ{F?>{y$sfqLN&$koTN%{LaA|)BgV{6RwXXIg-^i?o8BS7Hlk9fB``aA8A>aJgAbk)fO_QA{BFv#A(~|j4hb_k>!mY_B47cli<L>-B?QvG=|fadHBj`9<+$2esOapAsr`K<m_rbTBDEY{hFgPk4dz*UUDDEY`NF`-(5lhV`pCy_&BAIcX$L_>0c>?f3Upm=H-et*3VH@&vFl7UJ@g&p{-tu!X_r%uI1T>?qaSc}4!Sq_CZp8kK<$~jfq1`2VFqz=(KrI00V>VzG3~ZK7NNkprL3yx6}vo&u8M}o%$Q|L=qfi_{Qnv=^%qaN&=up_#3{-irk5V+^H}7cbRtreql3Nk6EIm$o(5Gi1-+0jNPUN4#EZ>7$W1R*nb&^U)psIQwK;j--U+0tX7Nd1S>&oe95sS*DS_j3#qI2pdKJtn7zhEV5|q*vxT+>`wOG0Wq8+ubGLctZ%8M}u1htU0?pHNQUNP*AWC`j;_LP!(C0q-lSWdf`gnUMqDVGef*raId6!%I9RY(=gWAzLw-rKQE7clr4a|7gRp`^*A_E1Xd3s^wTazx@#-U=1O!X&Rhn7(Ur5mzWgwy#?1YQz}Q5?VJcT3?`=nld?w%;P*D-3Nyjq^dGvP!u4M^b9W&%4<9kR^-dXBQIpsu8}lXBIR52R2kiyy4sG&j^iaYDEqN(4;PV#Aw<ISU1}cK_T$pc_ST?MS&Z?*9a*i}5FtxMCxFOL`!p!l8|B_`jUJ9AY<&fPDR0c=7J>`JyCyf8d{t4kDrWQm{?R=1PUvZ(e#CC8Vmy?aW{|0QrkW^>I5ku<{otYmtmI^$UM!ZG1w)bgAU)VGa%0<VNw)sw(CTKB!MPUdfEaPRS4#n0_fG*7AcS7@FV$5$AqNcDF$L8u`!6m1eeDdvD$Po#;Al8gs;elNCAoB|^)8bBaE3@Hl*|G|EG5q3VOlLkQL$+s@wm*?uPfD|3;#W;ZZpL=BT;xiP1PL!a8B1Hy&|T&CC?vYYv?LP6Rl@knRnmK%d(m`D-0^ZGdLJ2;xhYXd#&r->DB3k^+|=A0uX>AQ<Z7mXrkWhR_*Uqrmi^^{iU7@rDuqIk!W=+G6pm!89H27nQj)O73a>m1YQn2=`cl&qjcL80HrWCl*)an5CPO!ratqIQWhCnKxr41M7o8v^Dp)NOJN4a+OjtknBcHLsz$|VThh>|uya+iXy^u^^L#Kd%<L^0A*2hm2N>aWg<JfQBjCAhZIYyrqqWrIE{x$1D10GtFD~Uk<1c-<%(U!bLI7D0UC`AY$D)@lfiiyEP%tZ)Dzz_~KcKbTyWQhb6%lh*DfsAt(qpBpYMg^cizrEt!}L;?tE#voH9NpS11Sqs<x_w}2|GTqeVXWplaS-sWcI|<n$f+^T*bv3<|-b{n+xYQ+$^~y%lDL18~jg6W$oe>FjQV+Gos_Ec~B<+N_DA$6lbuQ8{LYAGFUWBiwmV$5}@dfT1j0O#>V!DQk^wIQWBZJRY(M^JSK}05hWSum#pu$D8rawu_=WlMZS`p@4L>zm7sJ6W6m&^AowYfK76pcyqoIsDU<D#kz`B+BUJNFznqqpEF3K_7=3~w*eWMZ4`;w}mdh7XSVXo3+Q?*5Mi-}}%c)XDWhtU6CrJkc?4=zqg5i?*v}JB<UPfDX#1q>mr-DC;(SU*}vaAPz7*SFy;KZvrhC6nVC@oA2P>{(WshFB_%A5%$NRT%`4&X=>OB$33$y$fn$l?KFi%gAas&|B2SlpYZp_Z{$HBtm-$ea(5Y^LGN#Rb>UA)#OmEd?Om;fsYH+JS3|>hTBk3tHCG&9)7rv%!uE!hUluLl=ThY>~K`f)`ydo41CNokn5qt;xw%v_pJ?!gpMpld+jY{#{0~;rcWpYdVfcg}9v~pYk<MA+ZKPG6A(D3R*hR?)s@iHO}F62Md6*Mv&K#1n)zgnZ->@)+rM$2D)s7Wn`Zu$TQcb(A!NW?bLpN_VSL4Uq@38F<Le=3(%_uheA%vCxUt@pf_2^@W=<M3e>^r+szfDl67GMke&3UX=g=~<Vb-rK^&e|B_YuMc5A7t8Akv2GpEXuBUmDrpbGc{zCW_5M@X1jx(c(v#V(53kAz~%v&US-h-X8?J(W6YTKhySI?|w{*`9E~w?F)l&A+o3BvX-9naER=q{63ZIs{0;=V0v+Xw|8r6xf7q<r`x`NlG1}@$^E1s+esURlQYni{%_k%NB}<og!2bpNSOzhKc9<Rh4L-K8BQOZRxopPb@GYIm0POyA(NZ78s)_`n<?Of+KS6B3K@Z(D=b?&n)4cIJ8$hEpZnWULzip<ipzauureX-TwU;|NQ$cd9=ST5=EoJO6lt9tmRoGs`~Nr<@6E)wzZjy36Otx`|)@Q$`P@B?!G?Q_C5AVBvMPdl*>w-rEe)nJ*~tO`9V?X#OS{=DLR`tM$AN;=xNAl1^}ijsqF@70kRG|U*`6Sf0uCO2S=FnB2xmAZ3dK3Z@$jOFoLRR9D38!Zjs9#`MlHxu#kbU18y2-MC6VJp}FkJBi~ONckXGMf&;<cpoyZc*iEtYhXVaf&9v0*Qo56Ad-)OopdJ`Ir4NG(;4hN7_S$vBZrEWV`*VJBsl{tq*W>j=uw!<#v%jHb7urYY|7_fJYNjrpO63jd{)h`-<~B*}@G#*)=3S?nK_O!IA2~Dm+~vy#)5I{aS#dtHZ0LFe1LlX?YL^4}JyIJPnqHc@QfVc-``J+=mu1&BxuSfhBj}8K#L#u6j19+f^>XAKM58Sc0&c9A6}(&uIN5ub`Z+YD%}Me9sIbsFfi#fdyC^GzFv80Udn*qC5m-ecArmlSlE-v`sCK$SE0gT9;2cMiH2AAnv$@B>115fs*ZpiEcjA`7pq5lJkA6!Yd;^*427#zIel8}_I4K)?V0)p~dLa=yQCJ^a%3|t_fSxQcmfe<BLmahO>56*P)(}#vVocNBdQ2?AENeMwfhVe_?J{*7JK>(ls=PzPD>KKx<A)Wo$K)Qh$if7PAYw)?Sl)20>au;Aey%gN2T>sRl<hqICYkr!Z;KNAMPS#(1zN?fs`Z1Cy(32~-$mX595_SCGC`sYYG%>|I*NxDPgP-pO$)P#WPRgF$JaXB4V*VD3Pw#h);rh1SEf<N*PMN#*Uu%g=l($}q;|zFfYWqvK!B_)nmz3NvXf$~J5|xBOY&>y+6j^qms}@Y!-~Ye*o&~js<_}a0k2_Mw25Q-a9e(vv&ilY7dE?WM^Y*?j~ZjRmKUWo)vcA_&y#KKAAp$-hY&zbJUaGE;)3aKdxgW`_>dHbJaH;NG#ZI~=yl?PVrL|eXNvejO_d^3UksgqIpa>py`4(KVu2lEnd-8&p+seJ)zF&B#6{56JRzH`l0B!vQJ%KlIx!vG+zBsbAq1nXs<MQ@E~<5&pe)h6B|&j`dBcj9=!b$@PM(6!=9J5nn9JxH#r8A9%l-2}!k8yE=ygV8ji&!73cZxsPz&axsoiRVK8(K=#$+jg=gn_Y%*XqgB<`L(#hLz`n6#%+YdMSeTombEt($OU+F}+OpFb*6=LD{&R%VjJ36<-emnMjETNyPa7NzM?=T8xqr$&;y|FXyIav_AZZ3krc0c}e)VPZ$Kr3<oxQGpqe6Tu|x%vdhd)s&Qo4A&pbuzo@$Jk#4{ll2$vTe3IFpX53*dy#1nnt=G8m>I_=kDcpLFjXRS#z`Jr<nJ{=9qZpTsz&H_?$TG&w7}GU0d1V*|7n7jhw|Lup_=WpRklcR<&2;<vd&D|2}&h7kq3>}6?yG={jgQV67F(3lX3n}s?oxiNltb(-LW2*<l(%XD#RhUXW0_i39XC(Q;g<>ZHTqBz18eL+-kW(Pa@@RxdwF<Q&r$`V|2k5{yUkaPXczkZQgj2c`yl?AV)ZyXUXc?R56GxNW9lfc1=N)-wA=ngCu~EVS*|A66Q>>%S`4BCH#Bl>Pl4!g>T8_TtLe15M=DrCsmXL^lGl+%6hd9tiQcmc&V1l&}2-yc9$t@gd1c(R<OBrH36yI;SrFq9v(@p1x7c3^Je<A^Jw$)i-Mkkrp`)Sslj=rGL|c{<Sj-}#tLW%uP>5ip=a)i=iFSv@0P|{8oAs!Gq%QIJj1qry1RY19ah|WPu>3ZXrJ~weJA+3(2c~usR{{>xkh?8%FsMKGwfW`VmJswN5?PA^wbM^yH&oGjels>6#22uy<&YykAZz#YRbpO!jzi_bUW9^rQE^jL!6xzHGXO%J^dfY!hP`"
        )
    ).decode("utf-8")
)

_SELLABLE = (
    "STRAWBERRY",
    "MELON",
    "MILK",
    "WOOL",
    "EGG",
    "TOMATO",
    "CARROT",
    "WHEAT",
    "FERTILIZER",
)

_FRONT_RUN_HORIZON = 1
_FRONT_RUN_ITEMS = ("MELON", "STRAWBERRY", "MILK", "WOOL")
_BASE_PRICE = {"MELON": 250, "STRAWBERRY": 120, "MILK": 160, "WOOL": 200}
_GLUT_WEIGHT = {"MELON": 3.5, "STRAWBERRY": 2.0, "MILK": 2.0, "WOOL": 3.2}
_LAST_STEP = -1
_CLONE_CONFIDENCE = 0


def _public_signature(farm):
    """Compact public fingerprint for detecting a mirrored build."""
    counts = {
        item: 0
        for item in (
            "COW",
            "SHEEP",
            "GOOSE",
            "WHEAT",
            "CARROT",
            "TOMATO",
            "STRAWBERRY",
            "MELON",
            "PASTURE",
            "COOP",
            "WEED",
        )
    }
    for row in farm.get("tiles", []) or []:
        for tile in row or []:
            if not isinstance(tile, dict):
                continue
            for key in ("animal", "crop", "kind"):
                value = tile.get(key)
                if value in counts:
                    counts[value] += 1
                    break
    positions = [farm.get("farmer", [0, 0]), *(farm.get("hands", []) or [])]
    return (
        len(farm.get("hands", []) or []),
        tuple(sorted(farm.get("unlocked_quadrants", []) or [])),
        tuple(sorted(tuple(position) for position in positions)),
        tuple(counts[item] for item in sorted(counts)),
    )


def _signature_distance(left, right):
    distance = abs(left[0] - right[0])
    distance += 3 * abs(len(left[1]) - len(right[1]))
    distance += sum(abs(a - b) for a, b in zip(left[3], right[3]))
    if left[2] != right[2]:
        distance += 2
    return distance


def _update_clone_profile(obs, step):
    global _CLONE_CONFIDENCE
    if step not in (4, 24) and not (step >= 48 and step % 24 == 0):
        return
    farms = obs.get("farms", []) or []
    if len(farms) < 2:
        return
    player = int(obs.get("player", 0) or 0)
    distance = _signature_distance(
        _public_signature(farms[player]),
        _public_signature(farms[1 - player]),
    )
    if distance <= 1:
        _CLONE_CONFIDENCE = min(8, _CLONE_CONFIDENCE + 1)
    elif distance <= 4:
        _CLONE_CONFIDENCE = max(0, _CLONE_CONFIDENCE - 1)
    else:
        _CLONE_CONFIDENCE = max(0, _CLONE_CONFIDENCE - 3)


def _front_run(action, obs, step):
    """Sell one premium line immediately before a clone's expected glut."""
    if _CLONE_CONFIDENCE < 2 or _FRONT_RUN_HORIZON <= 0:
        return
    orders = list(action.get("market", []) or [])
    if len(orders) >= 10:
        return
    already = {}
    for order in orders:
        if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
            already[order[1]] = already.get(order[1], 0) + max(0, int(order[2] or 0))
    planned = {}
    end = min(len(_TRACE), step + _FRONT_RUN_HORIZON + 1)
    for future_step in range(step + 1, end):
        distance = future_step - step
        for order in _TRACE[future_step].get("market", []) or []:
            if not (
                isinstance(order, list)
                and len(order) >= 3
                and order[0] == "SELL"
                and order[1] in _FRONT_RUN_ITEMS
            ):
                continue
            item = order[1]
            quantity = max(0, int(order[2] or 0))
            if item not in planned:
                planned[item] = [distance, quantity]
            else:
                planned[item][1] += quantity
    shed = (obs.get("private") or {}).get("shed") or {}
    prices = (obs.get("market") or {}).get("prices") or {}
    choices = []
    for item, (distance, quantity) in planned.items():
        available = max(0, int(shed.get(item, 0) or 0) - already.get(item, 0))
        quantity = min(available, quantity)
        if quantity <= 0:
            continue
        price = float(prices.get(item, _BASE_PRICE[item]) or 0)
        priority = (
            price * quantity * _GLUT_WEIGHT[item]
            + (_FRONT_RUN_HORIZON + 1 - distance) * _BASE_PRICE[item]
        )
        choices.append((priority, item, quantity))
    if choices:
        _, item, quantity = max(choices)
        orders.append(["SELL", item, quantity])
        action["market"] = orders[:10]


def _terminal_liquidation(action, obs, step):
    """Replay-derived safety net: leave no sellable shed inventory at season end."""
    if step < 680:
        return
    shed = (obs.get("private") or {}).get("shed") or {}
    market = action.setdefault("market", [])
    already = {
        order[1]
        for order in market
        if isinstance(order, list) and len(order) >= 2 and order[0] == "SELL"
    }
    for item in _SELLABLE:
        qty = int(shed.get(item, 0) or 0)
        if qty > 0 and item not in already and len(market) < 10:
            market.append(["SELL", item, qty])


def _shed_access(size):
    half = size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def _move_toward(pos, target, tiles):
    x, y = pos
    tx, ty = target
    choices = []
    if tx < x:
        choices.append(("WEST", (x - 1, y)))
    if tx > x:
        choices.append(("EAST", (x + 1, y)))
    if ty < y:
        choices.append(("NORTH", (x, y - 1)))
    if ty > y:
        choices.append(("SOUTH", (x, y + 1)))
    size = len(tiles)
    for op, (nx, ny) in choices:
        if 0 <= nx < size and 0 <= ny < size and tiles[ny][nx] != "LOCKED":
            return [op]
    return ["PASS"]


def _terminal_action(obs):
    """Observation-driven final-eight-turn harvest/drop/sell controller."""
    player = int(obs.get("player", 0) or 0)
    farm = (obs.get("farms") or [])[player]
    private = obs.get("private") or {}
    tiles = farm.get("tiles") or []
    size = len(tiles)
    positions = [farm.get("farmer", [0, 0]), *(farm.get("hands") or [])]
    inventories = list(private.get("inventories") or [])
    inventories.extend({} for _ in range(len(positions) - len(inventories)))
    sheds = set(_shed_access(size))

    available = {
        (x, y)
        for y, row in enumerate(tiles)
        for x, tile in enumerate(row)
        if isinstance(tile, dict) and int(tile.get("yield_units", 0) or 0) > 0
    }
    actions = []
    pending = {}
    for pos_raw, inventory in zip(positions, inventories):
        pos = tuple(pos_raw)
        inventory = inventory or {}
        load = sum(max(0, int(v or 0)) for v in inventory.values())
        x, y = pos
        tile = tiles[y][x] if 0 <= y < size and 0 <= x < size else None
        if load > 0 and pos in sheds:
            action = ["DROP"]
            for item, count in inventory.items():
                if item in _SELLABLE:
                    pending[item] = pending.get(item, 0) + max(0, int(count or 0))
        elif isinstance(tile, dict) and int(tile.get("yield_units", 0) or 0) > 0:
            action = ["HARVEST"]
            available.discard(pos)
        elif load > 0:
            target = min(sheds, key=lambda q: abs(q[0] - x) + abs(q[1] - y))
            action = _move_toward(pos, target, tiles)
        elif available:
            target = min(available, key=lambda q: (abs(q[0] - x) + abs(q[1] - y), q[1], q[0]))
            available.discard(target)
            action = _move_toward(pos, target, tiles)
        elif isinstance(tile, dict) and tile.get("fertilizer_available", False):
            action = ["COLLECT_FERTILIZER"]
        else:
            action = ["PASS"]
        actions.append(action)

    shed = dict(private.get("shed") or {})
    for item, count in pending.items():
        shed[item] = int(shed.get(item, 0) or 0) + count
    prices = (obs.get("market") or {}).get("prices") or {}
    sells = [
        (
            int(shed.get(item, 0) or 0) * int(prices.get(item, 1) or 1),
            item,
            int(shed.get(item, 0) or 0),
        )
        for item in _SELLABLE
    ]
    sells = [row for row in sells if row[2] > 0]
    sells.sort(reverse=True)
    market = [["SELL", item, qty] for _, item, qty in sells[:10]]
    if int(obs.get("hour", 0) or 0) <= 1:
        already = int(farm.get("hires_today", 0) or 0)
        for _ in range(min(10 - len(market), max(0, 8 - already))):
            market.append(["HIRE"])
    return {"farmer": actions[0], "hands": actions[1:], "market": market[:10]}


def _base_agent(obs, config=None):
    global _LAST_STEP, _CLONE_CONFIDENCE
    step = min(int(obs.get("step", 0) or 0), len(_TRACE) - 1)
    if step == 0 or step <= _LAST_STEP:
        _CLONE_CONFIDENCE = 0
    _LAST_STEP = step
    _update_clone_profile(obs, step)
    if step >= 717:
        return _terminal_action(obs)
    action = copy.deepcopy(_TRACE[step])
    _front_run(action, obs, step)
    _terminal_liquidation(action, obs, step)
    return action


# ===========================================================================
# Market-controller overlay
# ===========================================================================
import math as _math

# Per-step remaining sell volume of this field plan, measured over c27 self-play.
_SUPPLY = json.loads(
    zlib.decompress(
        base64.b85decode(
            "c%1Fr%Wm5+5Cza*39{~j!?(Ii3pWj#)PQRsXp4SH(SNTlZOK$D%hrRG91k$}ECK|GWl5pP5&z!5eqB9m??2xC_S${8>%g|40o8~KRn)i|T_c-Ng)B~CGN496wl}hgs1QXm@KJ@zO8JSLEoMTcp!~L+F{jWC^e|LF)=(2sf$PIb3(SlNzsDBEF#JfoWe(t$Yj9w9c;Cbw<7UNFSXW_+8eK!jXnZ0v6}ZhU25LvUVmLTB{V)npQt&Tu2T?{8u6>1DeP;Bfh-txjrG(rgadmg#C&QQ5mb7*zObT%PjIEHq#)0xwmcrH0IS6;r%ds_7fjeO<R-XVDHtFe5b{U9c@TIh4Qa~f2^712`IfKEUA#@B*lD={N5Gf8RziqLrKOgSyKR;|X>+lpP>YsCQadB~Rad9Oo3_rH(mxt||haX&ATwGjSTv-akk00C3!|SKjX7dw65Q*tshG7_nVVGkyprl}RZvx~bgg>YpF-fdKOSG4qgU%8bqxwVs6t+gzh!`qtez1P$MN(W?6824OUyMG5Y$A?9(^>?+g>mRks6oAK>ZeGxbZYtsodn6F-$d?$<E};~EL)F^?O7_S=&9^w^}PO$2eRE-I>Ru`&4T`{s6B{cFwQ{YZl6U*zQ14uWyS3#%h2Z*@^*MPQP3v8n8;y4cWAPRbdmZHJgFv)oG)UwHJsJsBlnMRadB~RadBm-FjM*T{4I2j>|PvW80OtT4e<Ic^F9%mLxt<aObni{eUSnSOm>`25B5IDhw)1T#~HJ2gbkb)it^`?XCZfm;OhyiIuT((rx*gdOtM5Af}2MpCW=~4u!#b8dq^Fe(W!z<VQjEXR6G?ub;2p#H~XpMB5DU|K3=`9*UzC3<m5IO40GEoV6^e>(Kih?vsxDB>cI}F?O-s7>4zgO*m=mOMPEO7fFHFt)1`zxoKzFEYZV<Sf2W`*g3~vl6)Si2btbe1*(mA?61N3mCrB|}<jgtQPJ>6GFRRV=>G|o`Y7^F*FlVr6C;{`%5t~lbSY!)lcb=RE!hfF_mzI-r-D(o354i67ZQuEZwrOsCA(S1oU{8hVL>-fNRvtUO?m%zt9OxwICh{0%a-kZ?nHV;0J{oL}oHQfG!C2wLe($Yu`<RKME{uGWj?HT?+Td1C5YbH5F*r?^*4GKtKIO3v+vWF6XxHyrn;6*2-<p>3c(Rs!pD~m+;RUgj8S*-S*aeT2QB@B!|NaA0p<>w"
        )
    ).decode("utf-8")
)

_I0 = 10000
_PRICE_FLOOR = 1
_MP = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT": (35, 450, "log", 0.20, "sqrt", 0.70),
    "TOMATO": (60, 200, "linear", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60),
    "EGG": (50, 332, "linear", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
_SHOP_DEMAND = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_CENTER_ITEMS = tuple(k for k in _MP if k != "FERTILIZER")

# Products the controller owns, mapped to a reservation price expressed as a
# fraction of base price. Everything else keeps the tape's schedule untouched.
_RESERVE = {}
# Sort SELL orders by gross value so the most valuable sale takes the earliest
# slot; market slots resolve index by index across both players.
_SORT_SELLS = True
# Ranking key for slot placement: "gross", "unit" or "impact".
_SORT_KEY = "impact"
# True places promoted sells ahead of buys/hires; False keeps the tape's layout.
_SELLS_FIRST = True
# Only these products may be promoted into early slots. Empty means all.
_PROMOTE = ("MILK", "WOOL", "STRAWBERRY", "MELON", "EGG", "TOMATO", "CARROT", "FERTILIZER")
# Extra slot priority for a product whose remaining supply outruns the town's
# remaining appetite. Such a product is a race, not a hold: its price will only
# fall, so the units sold before the opponent's are the only ones worth much.
# Ranking purely by current price gets this backwards — a already-crashed product
# looks unimportant precisely when beating the opponent to the floor matters most.
_RACE_WEIGHT = 0.0
# Products that may be promoted only from this step onward. Selling wheat early
# lowers the price an opponent pays for feed, which can rescue a cash-starved
# rival; deferring wheat promotion keeps that pressure on during the early game
# when starvation actually bites.
_PROMOTE_AFTER = {}
# Products promoted only while the opponent's public money is at least this much.
# A rival near insolvency is the one most helped by our extra supply, so we hold
# that pressure on until they are clearly solvent.
_PROMOTE_IF_OPP_MONEY = {"WHEAT": 200.0}
# Force selling once the shed reaches this load, protecting end-of-day drops.
_SHED_PRESSURE = 80
# Reservation decays linearly to zero across this window, spreading liquidation.
_RAMP_START = 576
_RAMP_END = 716

_SUPPLY_DRIVER = {
    "MILK": ("animal", "COW"),
    "WOOL": ("animal", "SHEEP"),
    "EGG": ("animal", "GOOSE"),
    "FERTILIZER": ("animal", None),
    "STRAWBERRY": ("crop", "STRAWBERRY"),
    "MELON": ("crop", "MELON"),
    "WHEAT": ("crop", "WHEAT"),
    "CARROT": ("crop", "CARROT"),
    "TOMATO": ("crop", "TOMATO"),
}


def _mshape(func, x):
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return _math.sqrt(x)
    if func == "log10":
        return _math.log10(1.0 + x)
    return _math.log(1.0 + x)


def _mprice(item, inventory):
    """Exact port of the engine's market_price."""
    base, throughput, below_f, below_t, above_f, above_t = _MP[item]
    if inventory < _I0:
        amp = below_t * base / _mshape(below_f, throughput)
        value = base + amp * _mshape(below_f, _I0 - inventory)
    else:
        amp = above_t * base / _mshape(above_f, throughput)
        value = base - amp * _mshape(above_f, inventory - _I0)
    return max(_PRICE_FLOOR, int(round(value)))


def _remaining_drain(item, step, shops):
    """Units of `item` the town consumes between `step` and the season end.

    Shops fire on steps divisible by 4, the town center on steps divisible by 12
    with multipliers that step up on days 10 and 20. Still-locked shops are
    credited from the day they are expected to unlock (one new shop every three
    days), so late-game demand is not understated.
    """
    if item == "FERTILIZER":
        return 0.0  # neither the shops nor the town center consume fertilizer
    unlocked = set(shops or ())
    live = 0
    pending = []
    for name, products in _SHOP_DEMAND.items():
        if item not in products:
            continue
        weight = 2 if len(products) == 1 else 1
        if name in unlocked:
            live += weight
        else:
            pending.append(weight)
    n_locked = len(_SHOP_DEMAND) - len(unlocked)
    pending_total = sum(pending)
    is_center = item in _CENTER_ITEMS
    total = 0.0
    for s in range(step, 720):
        day = s // 24
        if s % 4 == 0:
            total += live
            if pending_total and n_locked > 0:
                expected = min(n_locked, max(0, day // 3 + 1 - len(unlocked)))
                total += pending_total * (expected / n_locked)
        if is_center and s % 12 == 0:
            total += 4 if day >= 20 else (2 if day >= 10 else 1)
    return total


def _count_driver(farm, kind, name):
    total = 0
    for row in farm.get("tiles") or []:
        for tile in row or []:
            if not isinstance(tile, dict):
                continue
            if kind == "animal":
                animal = tile.get("animal")
                if animal and (name is None or animal == name):
                    total += 1
            elif tile.get("kind") == "PLANT" and tile.get("crop") == name:
                total += 1
    return total


def _opponent_scale(obs, item):
    """Opponent's expected remaining supply of `item`, relative to ours."""
    driver = _SUPPLY_DRIVER.get(item)
    if driver is None:
        return 1.0
    farms = obs.get("farms") or []
    if len(farms) < 2:
        return 1.0
    me = int(obs.get("player", 0) or 0)
    kind, name = driver
    mine = _count_driver(farms[me], kind, name)
    theirs = _count_driver(farms[1 - me], kind, name)
    if mine <= 0:
        return 1.0 if theirs > 0 else 0.0
    return max(0.0, min(2.0, theirs / float(mine)))


def _reserve_price(item, step, obs, shops):
    """Reservation price for one unit of `item`.

    A fixed fraction of base price, decayed linearly to zero over the
    liquidation ramp, and scaled down when the town's remaining appetite cannot
    absorb the supply still to come: a structurally oversupplied product is a
    race to sell, not something to hold.
    """
    base = _MP[item][0]
    frac = _RESERVE[item]
    if step >= _RAMP_START:
        span = float(max(1, _RAMP_END - _RAMP_START))
        frac *= max(0.0, (_RAMP_END - step) / span)
    drain = _remaining_drain(item, step, shops)
    supply = float(_SUPPLY.get(item, [0] * 721)[min(step, 720)])
    ahead = supply * (1.0 + _opponent_scale(obs, item))
    if ahead > 0.0:
        frac *= min(1.0, drain / ahead)
    return base * frac


def _plan_sells(obs, step, slots, short_of_cash):
    """Choose SELL orders for the controlled products."""
    if slots <= 0:
        return []
    shed = (obs.get("private") or {}).get("shed") or {}
    inventory = (obs.get("market") or {}).get("inventory") or {}
    shops = (obs.get("town") or {}).get("unlocked_shops") or []
    load = sum(max(0, int(v or 0)) for v in shed.values())
    forced = load >= _SHED_PRESSURE or short_of_cash > 0

    candidates = []
    for item in _RESERVE:
        held = int(shed.get(item, 0) or 0)
        if held <= 0:
            continue
        inv = int(inventory.get(item, _I0) or _I0)
        if forced:
            units = held
        else:
            reserve = _reserve_price(item, step, obs, shops)
            units = 0
            while units < held and _mprice(item, inv + units) >= reserve:
                units += 1
        if units > 0:
            candidates.append((_mprice(item, inv) * units, item, units))
    candidates.sort(reverse=True)
    return [["SELL", item, units] for _, item, units in candidates[:slots]]


def _cash_needed(orders, obs):
    """Coins this turn's buy orders require."""
    seeds = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
    animals = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
    prices = (obs.get("market") or {}).get("prices") or {}
    total = 0
    for order in orders:
        if not isinstance(order, list) or not order:
            continue
        op = order[0]
        if op == "BUY_SEED" and len(order) >= 3:
            total += seeds.get(order[1], 0) * int(order[2] or 0)
        elif op == "BUY_ANIMAL" and len(order) >= 3:
            total += animals.get(order[1], 0) * int(order[2] or 0)
        elif op == "BUY_PRODUCT" and len(order) >= 3:
            total += int(prices.get(order[1], 50) or 50) * int(order[2] or 0)
        elif op == "BUY_LAND":
            total += 4000
    return total


def _race_factor(item, step, obs):
    """1.0 when the town can absorb everything still coming, higher when not."""
    if _RACE_WEIGHT <= 0.0:
        return 1.0
    shops = (obs.get("town") or {}).get("unlocked_shops") or []
    drain = _remaining_drain(item, step, shops)
    supply = float(_SUPPLY.get(item, [0] * 721)[min(step, 720)])
    ahead = supply * (1.0 + _opponent_scale(obs, item))
    if ahead <= 0.0:
        return 1.0
    glut = max(0.0, 1.0 - drain / ahead)
    return 1.0 + _RACE_WEIGHT * glut


def _sell_priority(order, obs, step=0):
    """Rank a SELL order for slot placement; higher goes into an earlier slot.

    Market slots resolve index by index across both players, so an order in an
    earlier slot is priced before the opponent's matching order in a later slot.
    ``gross`` ranks by revenue at stake. ``impact`` ranks by how much revenue is
    actually lost by going second, which is the quantity times this order's own
    price impact — that promotes steep premium curves (wool, melon, milk) over
    large but nearly flat staple sales (wheat, egg).
    """
    if not (isinstance(order, list) and len(order) >= 3 and order[0] == "SELL"):
        return -1.0
    item = order[1]
    try:
        qty = int(order[2] or 0)
    except (TypeError, ValueError):
        return -1.0
    if qty <= 0 or item not in _MP:
        return -1.0
    inventory = (obs.get("market") or {}).get("inventory") or {}
    inv = int(inventory.get(item, _I0) or _I0)
    unit = _mprice(item, inv)
    held = int(((obs.get("private") or {}).get("shed") or {}).get(item, 0) or 0)
    qty = min(qty, held) if held > 0 else qty
    race = _race_factor(item, step, obs)
    if _SORT_KEY == "unit":
        return float(unit) * race
    if _SORT_KEY == "impact":
        return float(qty) * float(unit - _mprice(item, inv + qty)) * race
    return float(unit) * float(qty) * race


def agent(obs, config=None):
    """c27 with its SELL layer partially replaced by the market controller."""
    action = _base_agent(obs, config)
    try:
        step = int(obs.get("step", 0) or 0)
        if step >= 717:
            return action  # proven terminal controller; leave untouched
        orders = list(action.get("market") or [])
        keep = [
            order
            for order in orders
            if not (
                isinstance(order, list)
                and len(order) >= 2
                and order[0] == "SELL"
                and order[1] in _RESERVE
            )
        ]
        player = int(obs.get("player", 0) or 0)
        money = float(((obs.get("farms") or [{}])[player]).get("money", 0) or 0)
        short = max(0.0, _cash_needed(keep, obs) - money)
        sells = _plan_sells(obs, step, 10 - len(keep), short)
        if not _SORT_SELLS:
            action["market"] = (sells + keep)[:10]
            return action

        def is_sell(o):
            return isinstance(o, list) and o and o[0] == "SELL"

        opp_money = None
        if _PROMOTE_IF_OPP_MONEY:
            farms = obs.get("farms") or []
            if len(farms) > 1:
                opp_money = float(farms[1 - player].get("money", 0) or 0)

        def promotable(o):
            if not is_sell(o):
                return False
            item = o[1]
            if item in _PROMOTE_IF_OPP_MONEY:
                if opp_money is None:
                    return False
                return opp_money >= _PROMOTE_IF_OPP_MONEY[item]
            if item in _PROMOTE_AFTER:
                return step >= _PROMOTE_AFTER[item]
            return not _PROMOTE or item in _PROMOTE

        # Only promotable sells compete for the earliest slots. WHEAT and
        # FERTILIZER are the only products an opponent can BUY_PRODUCT, so
        # promoting those ahead of their buys would lower the price they pay for
        # feed; those sells are deliberately left in their tape position, where
        # the opponent's buys have already drained inventory and lifted the price.
        merged = [o for o in sells if promotable(o)] + [o for o in keep if promotable(o)]
        merged.sort(key=lambda o: -_sell_priority(o, obs, step))
        rest = [o for o in sells if not promotable(o)] + [o for o in keep if not promotable(o)]
        if _SELLS_FIRST:
            action["market"] = (merged + rest)[:10]
        else:
            # Keep the tape's slot layout: sorted sells refill the slots that
            # already held promotable sells; every other order stays put.
            out = []
            queue = list(merged)
            for order in keep:
                out.append(queue.pop(0) if (promotable(order) and queue) else order)
            out.extend(queue)
            action["market"] = out[:10]
        return action
    except Exception:
        return action
