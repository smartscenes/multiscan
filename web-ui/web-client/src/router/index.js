import Vue from 'vue'
import VueRouter from 'vue-router'
import ScansPage from "@/components/ScansPage/index";
import AnnotationsPage from "@/components/AnnotationsPage/index";
import GroupViewPage from "@/components/GroupViewPage/index";

Vue.use(VueRouter)

const routes = [
    {
        path: '/',
        redirect: '/scans',
    },
    {
        path: '/scans',
        name: 'ScansPage',
        component: ScansPage,
    },
    {
        path: '/annotations',
        name: 'AnnotationsPage',
        component: AnnotationsPage,
    },
    {
        path: '/group_view',
        name: 'GroupViewPage',
        component: GroupViewPage,
    },
]

const router = new VueRouter({
    routes
})

export default router
