(function(t){function e(e){for(var i,n,r=e[0],l=e[1],c=e[2],x=0,d=[];x<r.length;x++)n=r[x],Object.prototype.hasOwnProperty.call(s,n)&&s[n]&&d.push(s[n][0]),s[n]=0;for(i in l)Object.prototype.hasOwnProperty.call(l,i)&&(t[i]=l[i]);p&&p(e);while(d.length)d.shift()();return o.push.apply(o,c||[]),a()}function a(){for(var t,e=0;e<o.length;e++){for(var a=o[e],i=!0,r=1;r<a.length;r++){var l=a[r];0!==s[l]&&(i=!1)}i&&(o.splice(e--,1),t=n(n.s=a[0]))}return t}var i={},s={app:0},o=[];function n(e){if(i[e])return i[e].exports;var a=i[e]={i:e,l:!1,exports:{}};return t[e].call(a.exports,a,a.exports,n),a.l=!0,a.exports}n.m=t,n.c=i,n.d=function(t,e,a){n.o(t,e)||Object.defineProperty(t,e,{enumerable:!0,get:a})},n.r=function(t){"undefined"!==typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},n.t=function(t,e){if(1&e&&(t=n(t)),8&e)return t;if(4&e&&"object"===typeof t&&t&&t.__esModule)return t;var a=Object.create(null);if(n.r(a),Object.defineProperty(a,"default",{enumerable:!0,value:t}),2&e&&"string"!=typeof t)for(var i in t)n.d(a,i,function(e){return t[e]}.bind(null,i));return a},n.n=function(t){var e=t&&t.__esModule?function(){return t["default"]}:function(){return t};return n.d(e,"a",e),e},n.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},n.p="";var r=window["webpackJsonp"]=window["webpackJsonp"]||[],l=r.push.bind(r);r.push=e,r=r.slice();for(var c=0;c<r.length;c++)e(r[c]);var p=l;o.push([0,"chunk-vendors"]),a()})({0:function(t,e,a){t.exports=a("56d7")},"0d2f":function(t,e,a){},"159a":function(t,e,a){t.exports=a.p+"img/pipeline.0c80c583.png"},"55a2":function(t,e,a){t.exports=a.p+"img/paper_stack.57d8f82f.png"},"56d7":function(t,e,a){"use strict";a.r(e);a("e260"),a("e6cf"),a("cca6"),a("a79d");var i=a("2b0e"),s=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("v-app",[a("v-app-bar",{attrs:{app:"",color:"#373638",dense:"",dark:"","elevate-on-scroll":""}},[a("v-app-bar-title",{staticClass:"d-none d-sm-flex",staticStyle:{width:"100px"}},[t._v("MultiScan")]),a("v-tabs",{staticClass:"ml-n9",attrs:{"align-with-title":""}},[a("v-spacer"),t._l(t.tabs,(function(e){return a("v-tab",{key:e.tab,attrs:{to:e.link}},[t._v(" "+t._s(e.tab)+" ")])})),a("v-tab",{attrs:{href:"https://spathi.cmpt.sfu.ca/projects/multiscan/multiscan-docs/annotation/index.html"}},[t._v(" Doc ")]),a("v-tab",{attrs:{href:"https://multiscan3d.github.io/"}},[t._v(" Data ")]),a("v-tab",{attrs:{href:"https://github.com/3dlg-hcvc/multiscan"}},[a("v-icon",{staticClass:"mr-sm-1",attrs:{size:"22"}},[t._v("mdi-github")]),a("span",{staticClass:"d-none d-sm-flex"},[t._v("Code")])],1)],2)],1),a("v-main",[a("router-view",{scopedSlots:t._u([{key:"default",fn:function(e){var i=e.Component;return[a("transition",{attrs:{name:"fade"}},[a(i,{directives:[{name:"scroll",rawName:"v-scroll:#scroll-target",value:t.onScroll,expression:"onScroll",arg:"#scroll-target"}],tag:"component"})],1)]}}])})],1)],1)},o=[],n={name:"App",data:function(){return{tabs:[{tab:"Home",link:"/"}],showBarTitle:!1}},methods:{onScroll:function(t){console.log(t.target.scrollTop)}}},r=n,l=a("2877"),c=a("6544"),p=a.n(c),x=a("7496"),d=a("40dc"),u=a("bb78"),m=a("132d"),v=a("f6c4"),h=a("2fa4"),f=a("71a3"),b=a("fe57"),g=a("269a"),y=a.n(g),_=a("f977"),w=Object(l["a"])(r,s,o,!1,null,null,null),C=w.exports;p()(w,{VApp:x["a"],VAppBar:d["a"],VAppBarTitle:u["a"],VIcon:m["a"],VMain:v["a"],VSpacer:h["a"],VTab:f["a"],VTabs:b["a"]}),y()(w,{Scroll:_["b"]});var S=a("f309");i["a"].use(S["a"]);var k=new S["a"]({}),j=a("8c4f"),X=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("v-container",{attrs:{fluid:""}},[a("iframe",{staticStyle:{position:"fixed",top:"0",left:"0",bottom:"0",right:"0",width:"100%",height:"100%",border:"none",margin:"0",padding:"0"},attrs:{src:"https://multiscan3d.github.io/"}})])},D=[],T={name:"DatasetVisPage",data:function(){return{dialog:!1,isTableLoading:!0,tooltipText:"Click to Copy Sample ID",tooltipColor:void 0,imgWidth:0,imgHeight:0,search:"",headers:[{text:"Scan ID",value:"id",class:"subtitle-2 font-weight-bold",width:"3%"},{text:"Textured Mesh",value:"textured_mesh",sortable:!1,filterable:!1,class:"subtitle-2 font-weight-bold",width:"14%"},{text:"Semantic Objects",value:"sem_obj_inst",sortable:!1,filterable:!1,class:"subtitle-2 font-weight-bold",width:"14%"},{text:"Semantic Parts",value:"sem_part_inst",sortable:!1,filterable:!1,class:"subtitle-2 font-weight-bold",width:"14%"},{text:"Semantic Object OBBs",value:"sem_obb",sortable:!1,filterable:!1,class:"subtitle-2 font-weight-bold",width:"14%"},{text:"Articulated Parts",value:"part_articulation",sortable:!1,filterable:!1,class:"subtitle-2 font-weight-bold",width:"14%"},{text:"Articulation Animations",value:"articulationAnim",sortable:!1,filterable:!1,class:"subtitle-2 font-weight-bold",width:"27%"}],tableData:[],scanIds:[],interactiveMeshDialog:{showDialog:!1,currentGltfURL:null,currentWebpURL:null}}},methods:{openInteractiveMeshDialog:function(t,e){this.interactiveMeshDialog.currentGltfURL=t,this.interactiveMeshDialog.currentWebpURL=e,this.interactiveMeshDialog.showDialog=!0},resetTooltipText:function(){this.tooltipText="Click to Copy Scan ID",this.tooltipColor=void 0},getColor:function(t){return"whole"===t?"#dde439":"partial"===t?"#f15095":"#6c604a"},copyID:function(t){var e=this;this.$copyText(t).then((function(){e.tooltipText="Copied",e.tooltipColor="success"}),(function(){e.tooltipText="Error, your browser environment does not support this operation",e.tooltipColor="error"}))},pauseCurrentVideo:function(t){var e=t.currentTarget;e.pause()},playCurrentVideo:function(t){if(this.playBtn){var e=t.currentTarget;e.play()}},getImgHeight:function(){var t=.15*this.$refs.rel_obj.$el.clientWidth;this.imgWidth=t+"px",this.imgHeight=.8*t+"px"},loadDatasetFile:function(){this.tableData=[],this.playBtn=!0,this.playbackRate=.5;for(var t=["scene_00024_00","scene_00024_01"],e=0,a=t;e<a.length;e++){var i=a[e],s="https://aspis.cmpt.sfu.ca/projects/multiscan/multiscan_examples",o=i;this.tableData.push({id:o,rm_type:"xxxxx",texturedMeshThumbnailUrl:s+"/"+o+"/"+o+"-texture.webp",semThumbnailUrl:s+"/"+o+"/"+o+"-instance.webp",obbThumbnailUrl:s+"/"+o+"/"+o+"-obb.webp",textured_mesh:s+"/"+o+"/"+o+"-texture.glb",sem_part_inst:s+"/"+o+"/"+o+"-instance.glb",sem_obb:s+"/"+o+"/"+o+"-obb.glb",articuMesh:s+"/"+o+"/"+o+"-articulation.glb",articuWebpUrl:s+"/"+o+"/"+o+"-articulation.webp",articuAnimWebpUrl1:s+"/"+o+"/"+o+"-animation-camera0.webp",articuAnimWebpUrl2:s+"/"+o+"/"+o+"-animation-camera1.webp",articuAnimWebpUrl3:s+"/"+o+"/"+o+"-animation-camera2.webp",articuAnimWebpUrl4:s+"/"+o+"/"+o+"-animation-camera3.webp"})}}},mounted:function(){this.loadDatasetFile(),this.isTableLoading=!1},watch:{}},z=T,B=(a("65e4"),a("a523")),M=Object(l["a"])(z,X,D,!1,null,null,null),V=M.exports;p()(M,{VContainer:B["a"]});var A=function(){var t=this,e=t.$createElement,i=t._self._c||e;return i("v-container",{staticClass:"pt-0",attrs:{fluid:"",id:"scroll-target"}},[i("div",{staticClass:"d-flex justify-center",staticStyle:{position:"relative","background-color":"#373638"}},[i("video",{staticStyle:{"pointer-events":"none"},attrs:{autoplay:"",muted:""},domProps:{muted:!0}},[i("source",{attrs:{src:a("b3ef"),type:"video/mp4"}})]),i("div",{staticStyle:{width:"100%",position:"absolute",top:"0",left:"0"}},[i("div",{staticClass:"mt-14 pa-4",staticStyle:{"max-width":"1200px",margin:"0 auto"}},[i("p",{staticClass:"white--text text-md-h4 text-h5  font-weight-medium"},[t._v("MultiScan")]),i("p",{staticClass:"white--text text-md-h5 text-subtitle-2"},[t._v("Scalable RGBD scanning for 3D environments with articulated objects")]),i("v-divider",{staticClass:"my-6",attrs:{dark:""}}),i("p",{staticClass:"white--text text-md-h6",staticStyle:{opacity:"0.6"}},[t._v(" Yongsen Mao  •   Yiming Zhang  •   "),i("a",{staticClass:"white--text",attrs:{href:"https://jianghanxiao.github.io/",target:"_blank"}},[t._v("Hanxiao Jiang")]),t._v("  •   "),i("a",{staticClass:"white--text",attrs:{href:"https://angelxuanchang.github.io/",target:"_blank"}},[t._v("Angel X. Chang")]),t._v("  •   "),i("a",{staticClass:"white--text",attrs:{href:"https://msavva.github.io/",target:"_blank"}},[t._v("Manolis Savva")])])],1)])]),i("v-row",{directives:[{name:"scroll",rawName:"v-scroll:#scroll-target",value:t.onScroll,expression:"onScroll",arg:"#scroll-target"}],staticClass:"px-3",staticStyle:{"max-width":"1200px",margin:"0 auto"}},[i("v-col",{staticClass:"mt-3 mb-3",attrs:{cols:"12"}},[i("p",{staticClass:"my-5 text-sm-subtitle-1 text-justify"},[t._v(" We introduce MultiScan, a scalable RGBD dataset construction pipeline leveraging commodity mobile devices to scan indoor scenes with articulated objects and web-based semantic annotation interfaces to efficiently annotate object and part semantics and part mobility parameters. We use this pipeline to collect 230 scans of 108 indoor scenes containing 9458 objects and 4331 parts. The resulting MultiScan dataset provides RGBD streams with per-frame camera poses, textured 3D surface meshes, richly annotated part-level and object-level semantic labels, and part mobility parameters. We validate our dataset on instance segmentation and part mobility estimation tasks and benchmark methods for these tasks from prior work. Our experiments show that part segmentation and mobility estimation in real 3D scenes remain challenging despite recent progress in 3D object segmentation. ")])]),i("v-col",{staticClass:"mb-6",attrs:{cols:"12"}},[i("div",{staticClass:"d-flex align-center"},[i("h3",{staticStyle:{width:"12%"}},[t._v("Pipeline")]),i("v-img",{staticStyle:{width:"88%"},attrs:{src:a("159a")}})],1)]),i("v-col",{staticClass:"mb-2",attrs:{cols:"12"}},[i("div",{staticClass:"d-flex align-center"},[i("h3",{staticStyle:{width:"12%"}},[t._v("Dataset")]),i("v-img",{staticStyle:{width:"88%"},attrs:{src:a("57b2")}})],1)]),i("v-col",{attrs:{cols:"12"}},[i("div",{staticClass:"d-flex align-center"},[i("h3",{staticStyle:{width:"12%"}},[t._v("Benchmark")]),i("v-img",{staticStyle:{width:"88%"},attrs:{src:a("be65")}})],1)]),i("v-col",{staticClass:"mt-7",attrs:{cols:"12",md:"6"}},[i("span",{staticClass:"text-h5 font-weight-medium"},[t._v("News")]),i("v-divider",{staticClass:"my-3"}),i("ul",{staticClass:"text-sm-subtitle-1 mt-8"},[i("li",[t._v("some text some text some text some text")]),i("li",[t._v("some text some text some text some text")]),i("li",[t._v("some text some text some text some text")]),i("li",[t._v("some text some text some text some text")]),i("li",[t._v("some text some text some text some text")])])],1),i("v-col",{staticClass:"mt-7",attrs:{cols:"12",md:"6"}},[i("span",{staticClass:"text-h5 font-weight-medium"},[t._v("Project Video")]),i("v-divider",{staticClass:"my-3"}),i("div",{staticClass:"aspect-ratio mt-3 mb-6"},[i("iframe",{ref:"youtube",staticStyle:{border:"0"},attrs:{src:"https://www.youtube.com/embed/",allow:"accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",allowfullscreen:""}})])],1),i("v-col",{attrs:{col:"12"}},[i("span",{staticClass:"text-h5 font-weight-medium"},[t._v("Paper and Bibtex")]),i("v-divider",{staticClass:"my-3"}),i("v-row",{staticClass:"my-5",attrs:{justify:"center",align:"center"}},[i("v-col",{attrs:{cols:"auto",sm:"4",md:"4",lg:"4",xl:"4"}},[i("div",[i("v-img",{staticClass:"mb-4",staticStyle:{margin:"0 auto"},attrs:{src:a("55a2"),width:"230px"}}),i("div",{staticClass:"d-flex justify-center"},[i("a",{staticClass:"font-weight-bold",staticStyle:{"font-size":"20px"},attrs:{href:""}},[t._v("[Paper]")]),i("span",{staticClass:"font-weight-bold mx-4",staticStyle:{color:"#005cbf"}},[t._v(" | ")]),i("a",{staticClass:"font-weight-bold",staticStyle:{"font-size":"20px"},attrs:{href:""}},[t._v("[Poster]")])])],1)]),i("v-col",{attrs:{cols:"12",sm:"8",md:"8",lg:"8",xl:"8"}},[i("span",{staticClass:"font-weight-bold",staticStyle:{color:"#005cbf","font-size":"20px"}},[t._v("Bibtex")]),i("v-sheet",{staticClass:"pa-2 mt-3 mb-6",staticStyle:{"line-height":"1.4","font-size":"13px","font-family":"monospace","font-weight":"300"},attrs:{color:"#eee",rounded:""},on:{mouseover:function(e){t.showCopyBtn=!0},mouseleave:t.resetCopyBtn}},[i("v-tooltip",{attrs:{top:""},scopedSlots:t._u([{key:"activator",fn:function(e){var a=e.on,s=e.attrs;return[i("v-btn",t._g(t._b({directives:[{name:"show",rawName:"v-show",value:t.showCopyBtn,expression:"showCopyBtn"}],staticStyle:{float:"right"},attrs:{small:"",outlined:"",color:t.copyBtnColor},on:{click:t.copyBibtex}},"v-btn",s,!1),a),[t.copied?i("v-icon",{attrs:{size:"17",color:"success"}},[t._v("mdi-check")]):i("v-icon",{attrs:{size:"17",color:"grey darken-1"}},[t._v("mdi-content-paste ")])],1)]}}])},[i("span",[t._v(t._s(t.tooltipText))])]),i("div",{staticClass:"pa-4"},[i("p",{staticStyle:{margin:"0"}},[t._v("@inproceedings{xxxxxxx,")]),i("p",{staticStyle:{margin:"0"}},[t._v("author = {xx, xxx and xx, xxx and xx, xxx x and xxx, xxx},")]),i("p",{staticStyle:{margin:"0"}},[t._v("title = {{ xxxxx}: xxxxx xxxxxx for xxxxx xxxxxxxxxx},")]),i("p",{staticStyle:{margin:"0"}},[t._v("booktitle = {xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx xxxxxxxxx (xxxxxxx)},")]),i("p",{staticStyle:{margin:"0"}},[t._v("month = {xxxxx},")]),i("p",{staticStyle:{margin:"0"}},[t._v("year = {xxxx}")]),i("p",{staticStyle:{margin:"0"}},[t._v("}")])])],1),i("span",{staticClass:"font-weight-bold",staticStyle:{color:"#005cbf","font-size":"20px"}},[t._v("Citation")]),i("p",[t._v("xxx, xxx, xxx, xxx "),i("b",[t._v("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx ")]),t._v("xxxx xxxx.")])],1)],1)],1),i("v-col",{attrs:{cols:"12"}},[i("span",{staticClass:"text-h5 font-weight-medium"},[t._v("Download")]),i("v-divider",{staticClass:"my-3"}),i("v-row",{staticClass:"mt-5",attrs:{justify:"space-around"}},[i("v-col",{attrs:{cols:"12",md:"3",sm:"6",lg:"3",xl:"3"}},[i("v-hover",{scopedSlots:t._u([{key:"default",fn:function(e){var a=e.hover;return[i("v-card",{attrs:{elevation:a?4:2}},[i("div",{staticClass:"d-flex flex-row align-center pa-3"},[i("v-icon",{staticClass:"mr-2",attrs:{size:"50"}},[t._v("mdi-folder")]),i("div",[i("p",{staticStyle:{margin:"0","font-size":"15px",opacity:"0.9"}},[t._v("XXXXXXXXX")]),i("p",{staticStyle:{margin:"0","font-size":"13px",opacity:"0.7"}},[t._v("Size: 80 GB")])])],1),i("v-divider"),i("v-btn",{staticStyle:{"text-decoration":"none"},attrs:{block:"",text:"",color:"primary",href:"https://aspis.cmpt.sfu.ca/projects/mirrors/mirror3d_zip_release/nyu.zip"}},[t._v(" Download ")])],1)]}}])})],1),i("v-col",{attrs:{cols:"12",md:"3",sm:"6",lg:"3",xl:"3"}},[i("v-hover",{scopedSlots:t._u([{key:"default",fn:function(e){var a=e.hover;return[i("v-card",{attrs:{elevation:a?4:2}},[i("div",{staticClass:"d-flex flex-row align-center pa-3"},[i("v-icon",{staticClass:"mr-2",attrs:{size:"50"}},[t._v("mdi-folder")]),i("div",[i("p",{staticStyle:{margin:"0","font-size":"15px",opacity:"0.9"}},[t._v("XXXXXXXXX")]),i("p",{staticStyle:{margin:"0","font-size":"13px",opacity:"0.7"}},[t._v("Size: 80 GB")])])],1),i("v-divider"),i("v-btn",{staticStyle:{"text-decoration":"none"},attrs:{block:"",text:"",color:"primary",href:"https://aspis.cmpt.sfu.ca/projects/mirrors/mirror3d_zip_release/nyu.zip"}},[t._v(" Download ")])],1)]}}])})],1),i("v-col",{attrs:{cols:"12",md:"3",sm:"6",lg:"3",xl:"3"}},[i("v-hover",{scopedSlots:t._u([{key:"default",fn:function(e){var a=e.hover;return[i("v-card",{attrs:{elevation:a?4:2}},[i("div",{staticClass:"d-flex flex-row align-center pa-3"},[i("v-icon",{staticClass:"mr-2",attrs:{size:"50"}},[t._v("mdi-folder")]),i("div",[i("p",{staticStyle:{margin:"0","font-size":"15px",opacity:"0.9"}},[t._v("XXXXXXXXX")]),i("p",{staticStyle:{margin:"0","font-size":"13px",opacity:"0.7"}},[t._v("Size: 858 MB")])])],1),i("v-divider"),i("v-btn",{staticStyle:{"text-decoration":"none"},attrs:{block:"",text:"",color:"primary",href:"https://aspis.cmpt.sfu.ca/projects/mirrors/mirror3d_zip_release/mp3d.zip"}},[t._v(" Download ")])],1)]}}])})],1),i("v-col",{attrs:{cols:"12",md:"3",sm:"6",lg:"3",xl:"3"}},[i("v-hover",{scopedSlots:t._u([{key:"default",fn:function(e){var a=e.hover;return[i("v-card",{attrs:{elevation:a?4:2}},[i("div",{staticClass:"d-flex flex-row align-center pa-3"},[i("v-icon",{staticClass:"mr-2",attrs:{size:"50"}},[t._v("mdi-folder")]),i("div",[i("p",{staticStyle:{margin:"0","font-size":"15px",opacity:"0.9"}},[t._v("XXXXXXXXX")]),i("p",{staticStyle:{margin:"0","font-size":"13px",opacity:"0.7"}},[t._v("Size: 100.3 MB")])])],1),i("v-divider"),i("v-btn",{staticStyle:{"text-decoration":"none"},attrs:{block:"",text:"",color:"primary",href:"https://aspis.cmpt.sfu.ca/projects/mirrors/mirror3d_zip_release/scannet.zip"}},[t._v(" Download ")])],1)]}}])})],1)],1)],1),i("v-col",{staticClass:"mt-7",attrs:{cols:"12"}},[i("span",{staticClass:"text-h5 font-weight-medium"},[t._v("Acknowledgements")]),i("v-divider",{staticClass:"my-3"}),i("p",{staticClass:"text-sm-subtitle-1 text-justify"},[t._v("This work was funded in part by a Canada CIFAR AI Chair, a Canada Research Chair, NSERC Discovery Grant, a research grant by Facebook AI Research, and enabled by support from WestGrid and Compute Canada. The iOS and Android scanning apps were developed by Zheren Xiao and Henry Fang. We thank Qirui Wu for his help in re-implementing PointGroup with the Minkowski engine and contributions to the minsu3D code repository. We also thank Zhen (Colin) Li for collecting additional scans, and Henry Fang, Armin Kavian, Han-Hung Lee, Zhen (Colin) Li, Weijie (Lewis) Lin, Sonia Raychaudhuri, and Akshit Sharma for helping to annotate data. ")]),i("p",{staticStyle:{"font-style":"italic","font-size":"13px"}},[t._v(" Last updated: 2022-10-23 ")])],1)],1)],1)},P=[],O={name:"MainPage",data:function(){return{showCopyBtn:!1,copied:!1,copyBtnColor:"grey lighten-1",tooltipText:"Copy",gitHubStars:"N/A"}},methods:{onScroll:function(t){console.log(t.target.scrollTop),console.log("?????????????????????")},resetCopyBtn:function(){this.showCopyBtn=!1,this.copied=!1,this.copyBtnColor="grey lighten-1",this.tooltipText="Copy"},copyBibtex:function(){var t=this,e="@inproceedings{mirror3d2021tan,\nauthor = {Tan, Jiaqi and Lin, Weijie and Chang, Angel X and Savva, Manolis},\ntitle = {{Mirror3D}: Depth Refinement for Mirror Surfaces},\nbooktitle = {Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},\nmonth = {June},\nyear = {2021}\n}";this.$copyText(e).then((function(){t.copyBtnColor="success",t.copied=!0,t.tooltipText="Copied"}))}},mounted:function(){}},W=O,R=(a("e127"),a("8336")),I=a("b0af"),L=a("62ad"),U=a("ce7e"),E=a("ce87"),H=a("adda"),G=a("0fd9"),$=a("8dd9"),N=a("3a2f"),F=Object(l["a"])(W,A,P,!1,null,"6a97708b",null),J=F.exports;p()(F,{VBtn:R["a"],VCard:I["a"],VCol:L["a"],VContainer:B["a"],VDivider:U["a"],VHover:E["a"],VIcon:m["a"],VImg:H["a"],VRow:G["a"],VSheet:$["a"],VTooltip:N["a"]}),y()(F,{Scroll:_["b"]});var Z=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[t._v("Similar to ScanNet, several boards")])},Y=[],q={name:"BenchmarkPage"},K=q,Q=Object(l["a"])(K,Z,Y,!1,null,"284e43ea",null),tt=Q.exports;i["a"].use(j["a"]);var et=new j["a"]({mode:"hash",routes:[{path:"/",component:J},{path:"/data",component:V},{path:"/benchmark",component:tt}]}),at=et,it=a("bc3a"),st=a.n(it),ot=a("4eb5"),nt=a.n(ot);i["a"].use(nt.a),i["a"].prototype.$http=st.a,i["a"].config.productionTip=!1,new i["a"]({router:at,vuetify:k,render:function(t){return t(C)},mounted:function(){document.dispatchEvent(new Event("render-event"))}}).$mount("#app")},"57b2":function(t,e,a){t.exports=a.p+"img/dataset.108abbd5.png"},"65e4":function(t,e,a){"use strict";a("0d2f")},"985d":function(t,e,a){},b3ef:function(t,e,a){t.exports=a.p+"media/background.3334323a.mp4"},be65:function(t,e,a){t.exports=a.p+"img/benchmark.5b3187b7.png"},e127:function(t,e,a){"use strict";a("985d")}});
//# sourceMappingURL=app.7ad8e97a.js.map