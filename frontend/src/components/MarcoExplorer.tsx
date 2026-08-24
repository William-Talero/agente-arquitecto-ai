import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import type { Catalogo } from "@/types";
import { CafCard } from "./cards/CafCard";
import { WafCard } from "./cards/WafCard";
import { CicloCard } from "./cards/CicloCard";
import { EstandaresCard } from "./cards/EstandaresCard";

export function MarcoExplorer({ catalogo }: { catalogo: Catalogo }) {
  return (
    <Tabs defaultValue="caf" className="w-full">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="caf">CAF</TabsTrigger>
        <TabsTrigger value="waf">Well-Architected</TabsTrigger>
        <TabsTrigger value="ciclo">Ciclo de vida</TabsTrigger>
        <TabsTrigger value="estandares">Vigente (GA)</TabsTrigger>
      </TabsList>
      <TabsContent value="caf">
        <CafCard titulo="Cloud Adoption Framework · Adopción de IA" fases={catalogo.fases_caf} />
      </TabsContent>
      <TabsContent value="waf">
        <WafCard titulo="Well-Architected · Cargas de trabajo de IA" pilares={catalogo.pilares_waf} />
      </TabsContent>
      <TabsContent value="ciclo">
        <CicloCard titulo="Ciclo de vida de la solución de IA" etapas={catalogo.ciclo_vida} />
      </TabsContent>
      <TabsContent value="estandares">
        <EstandaresCard
          titulo="Estándares vigentes de Microsoft (GA)"
          revisado={catalogo.estandares_revisado}
          estandares={catalogo.estandares ?? []}
        />
      </TabsContent>
    </Tabs>
  );
}
